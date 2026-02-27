# agent.py
import os
from typing import Annotated
from typing_extensions import TypedDict

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, AnyMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from tools.get_course_info_tools import get_course_info
from tools.confirm_enrollment_tools import confirm_enrollment
from tools.save_user_details_tools import save_user_details
from utils.logger import get_logger
from utils.config import GROQ_API_KEY, MODEL_NAME

logger = get_logger(__name__)

#  System Prompt 
system_prompt = """You are CourseBot — a friendly sales assistant for a Generative AI education platform.

AVAILABLE COURSES:
   genai_beginner  — Generative AI for Beginners       ₹3,999  4 weeks
   genai_advanced  — Advanced GenAI & Agentic Systems  ₹12,499 8 weeks
   llmops          — LLMOps & DevOps for AI            ₹8,299  6 weeks

TOOLS YOU HAVE:
   get_course_info     → use when user asks about a course
   confirm_enrollment  → use when you have ALL 5 fields collected
   save_user_details   → use ONLY after confirm_enrollment returns "confirmed"

STEPS:
 Greet user warmly
 Understand what they want
 Use get_course_info tool to show course details
 Collect these ONE BY ONE — name, email, address, qualification, course
 When all 5 collected — call confirm_enrollment tool
 If confirmed → call save_user_details
 If cancelled → ask what to change

STRICT RULES:
- ONE field at a time — never ask multiple fields together
- Never hardcode course details — use get_course_info tool
- NEVER use **, __, *, _ around ANY text especially email addresses
- Never repeat the same information multiple times in one response
- Never skip confirm_enrollment before save_user_details
"""

#  Tools 
tools = [get_course_info, confirm_enrollment, save_user_details]


#  State 
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


# LLM 
def _build_llm():
    if not GROQ_API_KEY:
        raise EnvironmentError("GROQ_API_KEY not found in .env!")
    if not MODEL_NAME:
        raise EnvironmentError("MODEL_NAME not found in .env!")
    logger.info(f"[Agent] Initializing Groq LLM — {MODEL_NAME}")
    llm = ChatGroq(
        model=MODEL_NAME,
        api_key=GROQ_API_KEY,
        temperature=0.7,
    )
    return llm.bind_tools(tools, parallel_tool_calls=False)


llm_with_tools = _build_llm()


#  Agent Node
def agent_node(state: State) -> dict:
    logger.info(f"[agent_node] Invoked with {len(state['messages'])} message(s).")
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    try:
        response = llm_with_tools.invoke(messages)
        logger.info("[agent_node] LLM responded.")
        return {"messages": [response]}
    except Exception as e:
        logger.warning(f"[agent_node] Tool call failed: {e}")
        # ⭐ Retry ONCE without tools — fixes "Failed to call a function" error
        try:
            logger.info("[agent_node] Retrying without tools...")
            llm_plain = ChatGroq(
                model=MODEL_NAME,
                api_key=GROQ_API_KEY,
                temperature=0.7,
            )
            response = llm_plain.invoke(messages)
            logger.info("[agent_node] Retry succeeded.")
            return {"messages": [response]}
        except Exception as e:
            logger.error(f"[agent_node] Retry also failed: {e}")
            return {"messages": [AIMessage(content="I'm sorry, something went wrong. Could you please try again?")]}


# Human Review Node — interrupt() lives here 
def human_review_node(state: State):
    """
    Runs BEFORE confirm_enrollment tool executes.
    Pauses graph using interrupt() and waits for human to type yes or no.
    """
    last_message = state["messages"][-1]
    tool_call    = last_message.tool_calls[0]
    args         = tool_call.get("args", {})

    # Build confirmation summary
    summary = (
        f"\n📋 Please confirm your enrollment details:\n\n"
        f"  👤 Name          : {args.get('name', 'N/A')}\n"
        f"  📧 Email         : {args.get('email', 'N/A')}\n"
        f"  🏠 Address       : {args.get('address', 'N/A')}\n"
        f"  🎓 Qualification : {args.get('qualification', 'N/A')}\n"
        f"  📚 Course        : {args.get('course', 'N/A')}\n\n"
        f"Do you want to proceed with enrollment? (yes / no)"
    )

    logger.info("[human_review_node] ⏸️  PAUSED — waiting for human confirmation!")

    # Graph PAUSES here — waits for human input
    human_response = interrupt(summary)

    logger.info(f"[human_review_node] Human replied: '{human_response}'")

    # User said YES 
    if human_response.strip().lower() in ["yes", "y", "yeah", "ok", "okay", "sure", "proceed"]:
        logger.info("[human_review_node] ✅ Confirmed — running confirm_enrollment tool!")
        return Command(goto="tools")   # ← run the tool now

    #  User said NO 
    else:
        logger.info("[human_review_node] ❌ Cancelled!")
        return Command(
            goto="agent",
            update={
                "messages": [AIMessage(
                    content="No problem! Enrollment cancelled. "
                            "Let me know if you want to change anything or choose a different course."
                )]
            }
        )


# Router 
def route_after_agent(state: State):
    """
    After agent_node decides:
    - No tool call        → END
    - confirm_enrollment  → human_review_node  (needs human confirmation!)
    - any other tool      → tools directly
    """
    last_message = state["messages"][-1]

    if not getattr(last_message, "tool_calls", None):
        return "__end__"

    tool_name = last_message.tool_calls[0].get("name", "")
    logger.info(f"[Router] Tool detected: '{tool_name}'")

    if tool_name == "confirm_enrollment":
        logger.info("[Router] → human_review_node")
        return "human_review_node"

    logger.info("[Router] → tools")
    return "tools"


# Build Graph 
def build_graph():
    builder = StateGraph(State)

    builder.add_node("agent",             agent_node)
    builder.add_node("tools",             ToolNode(tools))
    builder.add_node("human_review_node", human_review_node)

    builder.add_edge(START, "agent")

    builder.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "human_review_node": "human_review_node",
            "tools":             "tools",
            "__end__":           END,
        }
    )

    builder.add_edge("tools", "agent")

    #  MemorySaver required for interrupt() to work!
    memory = MemorySaver()
    graph  = builder.compile(checkpointer=memory)

    logger.info("[Graph] Human-in-the-Loop graph compiled! ✅")
    return graph
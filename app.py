#app.py
import json
import uuid
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.types import Command

from agent import build_graph
from utils.logger import get_logger

logger = get_logger(__name__)

app   = FastAPI(title="GenAI Course Chatbot API", version="1.0.0")
graph = build_graph()

logger.info("[App] LangGraph agent ready")


class ChatRequest(BaseModel):
    message:      str
    chat_history: list = []
    session_id:   str  = ""    


@app.post("/chat")
async def send_messages(payload: ChatRequest):
    """Handle incoming chat messages and stream response."""

    query        = payload.message
    chat_history = payload.chat_history
    session_id   = payload.session_id or str(uuid.uuid4())

    chat_history.append({"role": "user", "content": query})

    logger.info(f"RECEIVED MESSAGE: {query} | session_id: {session_id}")

    #  thread_id keeps graph memory alive between requests
    config = {"configurable": {"thread_id": session_id}}

    async def event_stream():

        streamed_text  = ""
        metadata_items = []
        full_text      = ""   

        messages = []
        for item in chat_history:
            if item["role"] == "user":
                messages.append(HumanMessage(content=item["content"]))
            else:
                messages.append(AIMessage(content=item["content"]))

        try:
            for chunk, _ in graph.stream(
                {"messages": messages},
                config=config,
                stream_mode="messages"
            ):
                # Normal text token 
                if isinstance(chunk, AIMessage) and chunk.content and not getattr(chunk, "tool_calls", None):
                    token = chunk.content

                    # ⭐ Fix leakage — skip any token containing <function=
                    if "<function=" in token or "function=" in token:
                        continue

                    streamed_text += token
                    yield json.dumps({"type": "response", "content": token}) + "\n"

                # Tool call metadata 
                if isinstance(chunk, AIMessage) and getattr(chunk, "tool_calls", None):
                    for tc in chunk.tool_calls:
                        metadata_items.append({
                            "tool_name": tc.get("name"),
                            "tool_args": tc.get("args", {})
                        })
                        logger.info(f"Tool Called: {tc.get('name')} | args: {tc.get('args')}")

                # Tool result 
                if isinstance(chunk, ToolMessage):
                    metadata_items.append({"tool_result": chunk.content[:300]})

            # Check if graph is INTERRUPTED (waiting for human) 
            graph_state = graph.get_state(config)

            if graph_state.interrupts:
                interrupt_msg = graph_state.interrupts[0].value

                logger.info("[App] Graph INTERRUPTED — waiting for human input!")

                # Tell Streamlit: graph paused, show confirmation!
                yield json.dumps({
                    "type":       "interrupt",
                    "content":    interrupt_msg,
                    "session_id": session_id
                }) + "\n"

            #  Metadata 
            yield json.dumps({"type": "metadata", "content": metadata_items}) + "\n"

            # History Update 
            updated_history = chat_history + [
                {"role": "assistant", "content": streamed_text}
            ]
            yield json.dumps({
                "type":         "history_update",
                "chat_history": updated_history,
                "session_id":   session_id
            }) + "\n"

            logger.info("[Stream] Done")

        except Exception as e:
            logger.error(f"[Stream] Error: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


#  Resume Endpoint — called when user types yes or no
@app.post("/resume")
async def resume_graph(payload: dict):
    """
    Human-in-the-Loop Resume Endpoint.
    When human types 'yes' or 'no' in Streamlit → this endpoint resumes the paused graph.
    """
    session_id     = payload.get("session_id")
    human_response = payload.get("human_response")

    logger.info(f"[Resume] session_id={session_id} | human_response='{human_response}'")

    config = {"configurable": {"thread_id": session_id}}

    async def resume_stream():
        streamed_text = ""

        try:
            # ⭐ Command(resume=...) resumes graph from interrupt point!
            for chunk, _ in graph.stream(
                Command(resume=human_response),
                config=config,
                stream_mode="messages"
            ):
                if isinstance(chunk, AIMessage) and chunk.content and not getattr(chunk, "tool_calls", None):
                    token = chunk.content

                    if "<function=" in token or "function=" in token:
                        continue

                    streamed_text += token
                    yield json.dumps({"type": "response", "content": token}) + "\n"

                if isinstance(chunk, AIMessage) and getattr(chunk, "tool_calls", None):
                    for tc in chunk.tool_calls:
                        logger.info(f"[Resume] Tool after resume: {tc.get('name')}")

            yield json.dumps({"type": "metadata",     "content": []}) + "\n"
            yield json.dumps({"type": "resume_done",  "content": streamed_text}) + "\n"

            logger.info("[Resume] Graph resumed and completed ✅")

        except Exception as e:
            logger.error(f"[Resume] Error: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    return StreamingResponse(resume_stream(), media_type="application/x-ndjson")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "GenAI Course Chatbot"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
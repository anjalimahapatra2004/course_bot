import sys
import logging
from langchain_core.messages import HumanMessage, AIMessage

from agent import build_graph, stream_response

from utils.logger import get_logger

logger = get_logger(__name__)
# Stream to Terminal 
def print_streaming(generator):
    
    full_response = ""
    print("\n🤖 CourseBot: ", end="", flush=True)

    for token in generator:
        print(token, end="", flush=True)   # stream token-by-token
        full_response += token

    print("\n")   # ← mandatory \\n after full streaming response
    return full_response


# Main Chat Loop 
def run_chatbot():
    print("\n🎓 GenAI Course Purchase Chatbot — Type 'quit' or 'exit' to end.\n")

    # Build the LangGraph agent
    try:
        graph = build_graph()
    except EnvironmentError as e:
        print(f" Setup error: {e}")
        print("👉 Make sure your .env file has: GROQ_API_KEY=your_key_here")
        sys.exit(1)

    chat_history = []   # stores HumanMessage / AIMessage objects

    logger.info("[Main] Chatbot session started.")

    while True:
        try:
            # Get user input 
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "bye"):
                print("\n Thanks for visiting! See you soon. Happy Learning! 🚀\n")
                logger.info("[Main] Session ended by user.")
                break

            # Stream agent response 
            generator = stream_response(graph, chat_history, user_input)
            full_response = print_streaming(generator)

            # Update chat history 
            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=full_response))

            logger.info(
                f"[Main] History updated. Total messages: {len(chat_history)}"
            )

        except KeyboardInterrupt:
            print("\n\nSession interrupted. Goodbye! \n")
            logger.info("[Main] Session interrupted via KeyboardInterrupt.")
            break

        except Exception as e:
            logger.error(f"[Main] Unexpected error: {e}", exc_info=True)
            print(f"\n Something went wrong: {e}\n")


# Entry Point 
if __name__ == "__main__":
    run_chatbot()
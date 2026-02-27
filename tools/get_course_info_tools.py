from langchain_core.tools import tool
from utils.logger import get_logger

logger = get_logger(__name__)

course_catalog = {
    "genai_beginner": {
        "name": "Generative AI for Beginners",
        "price": "₹3,999",
        "duration": "4 weeks",
        "syllabus": ["Prompt Engineering", "ChatGPT APIs", "LangChain Basics", "RAG Intro"],
        "eligibility": "Anyone with basic computer knowledge",
    },
    "genai_advanced": {
        "name": "Advanced Generative AI & Agentic Systems",
        "price": "₹12,499",
        "duration": "8 weeks",
        "syllabus": ["LangGraph", "Multi-Agent Systems", "Fine-Tuning LLMs", "Vector DBs", "Production Deployment"],
        "eligibility": "Basic Python & ML knowledge required",
    },
    "llmops": {
        "name": "LLMOps & DevOps for AI",
        "price": "₹8,299",
        "duration": "6 weeks",
        "syllabus": ["CI/CD for LLMs", "Monitoring", "Docker & Kubernetes", "Cloud Deployment"],
        "eligibility": "DevOps or backend experience recommended",
    },
}


@tool
def get_course_info(course_key: str) -> str:
    """
    Fetches detailed information about a specific Generative AI course.

    Args:
        course_key (str): The course identifier. One of:
                          'genai_beginner', 'genai_advanced', 'llmops'.
                          Pass 'all' to list every available course.

    Returns:
        str: A formatted string with course details or a list of all courses.
    """
    try:
        logger.info(f"[get_course_info] Called with course_key='{course_key}'")

        if course_key == "all":
            result_lines = ["Available Generative AI Courses:\n"]
            for key, info in course_catalog.items():
                result_lines.append(
                    f"  [{key}] {info['name']} — {info['price']} | {info['duration']}"
                )
            result = "\n".join(result_lines)
            logger.info("[get_course_info] Returned full course catalog.")
            return result

        course = course_catalog.get(course_key.lower())
        if not course:
            msg = (
                f"Course '{course_key}' not found. "
                f"Available options: {', '.join(course_catalog.keys())}"
            )
            logger.warning(f"[get_course_info] {msg}")
            return msg

        syllabus_str = " -> ".join(course["syllabus"])
        result = (
            f"Course: {course['name']}\n"
            f"Price: {course['price']}\n"
            f"Duration: {course['duration']}\n"
            f"Syllabus: {syllabus_str}\n"
            f"Eligibility: {course['eligibility']}"
        )
        logger.info(f"[get_course_info] Successfully returned info for '{course_key}'.")
        return result

    except Exception as e:
        logger.error(f"[get_course_info] Unexpected error: {e}")
        return f"Error fetching course info: {str(e)}"
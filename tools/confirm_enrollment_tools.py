from langchain_core.tools import tool
from utils.logger import get_logger

logger = get_logger(__name__)


@tool
def confirm_enrollment(
    name: str,
    email: str,
    address: str,
    qualification: str,
    course: str
) -> str:
    """
    Shows enrollment summary and asks human to confirm before saving.
    Call this tool FIRST when you have all 5 fields collected.
    After human confirms — then call save_user_details.

    Args:
        name          (str): Full name of the user.
        email         (str): Email address of the user.
        address       (str): Residential address of the user.
        qualification (str): Highest qualification of the user.
        course        (str): Course key the user wants to enroll in.

    Returns:
        str: Summary of enrollment details for human to confirm.
    """
    logger.info(f"[confirm_enrollment] Called for user='{name}', course='{course}'")

    summary = (
        f"📋 Please confirm enrollment details before saving:\n\n"
        f"  👤 Name          : {name}\n"
        f"  📧 Email         : {email}\n"
        f"  🏠 Address       : {address}\n"
        f"  🎓 Qualification : {qualification}\n"
        f"  📚 Course        : {course}\n\n"
        f"Do you want to proceed with enrollment? (yes / no)"
    )

    logger.info(f"[confirm_enrollment] Summary built — returning to agent for human decision.")
    return summary
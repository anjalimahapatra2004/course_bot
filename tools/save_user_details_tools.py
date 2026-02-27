import json
import os
from datetime import datetime
from langchain_core.tools import tool
from utils.logger import get_logger

logger = get_logger(__name__)

storage_file = "enrolled_users.json"


def load_existing_users() -> list:
    if os.path.exists(storage_file):
        with open(storage_file, "r") as f:
            return json.load(f)
    return []


def save_users(users: list) -> None:
    with open(storage_file, "w") as f:
        json.dump(users, f, indent=2)


@tool
def save_user_details(
    name: str,
    email: str,
    address: str,
    qualification: str,
    course: str
) -> str:
    """
    Saves the user's enrollment details after they decide to purchase a course.

    Args:
        name          (str): Full name of the user.
        email         (str): Valid email address of the user.
        address       (str): Residential address of the user.
        qualification (str): Highest educational qualification of the user.
        course        (str): The course key the user wants to enroll in.

    Returns:
        str: Confirmation message with enrollment ID.
    """
    try:
        logger.info(f"[save_user_details] Saving details for user='{name}', email='{email}', course='{course}'")

        if not all([name, email, address, qualification, course]):
            msg = "All fields are required: name, email, address, qualification, course."
            logger.warning(f"[save_user_details] Validation failed — {msg}")
            return f"{msg}"

        if "@" not in email or "." not in email:
            msg = f"Invalid email format: '{email}'"
            logger.warning(f"[save_user_details] {msg}")
            return msg

        enrollment_id = f"ENR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        user_record = {
            "enrollment_id": enrollment_id,
            "name": name,
            "email": email,
            "address": address,
            "qualification": qualification,
            "course": course,
            "enrolled_at": datetime.now().isoformat(),
        }

        users = load_existing_users()
        users.append(user_record)
        save_users(users)

        logger.info(f"[save_user_details] Enrollment successful! ID={enrollment_id}")

        return (
            f"Enrollment Successful!\n"
            f"Welcome, {name}!\n"
            f"Enrollment ID : {enrollment_id}\n"
            f"Email         : {email}\n"
            f"Course        : {course}\n"
            f"Address       : {address}\n"
            f"Qualification : {qualification}\n"
            f"Our team will reach out to you at {email} with next steps. Good luck!"
        )

    except Exception as e:
        logger.error(f"[save_user_details] Error: {e}")
        return f"Error saving enrollment details: {str(e)}"
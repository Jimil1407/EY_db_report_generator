"""
Configuration and setup for the application.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_environment():
    """Load environment variables from .env.local file."""
    env_path = Path(__file__).parent / ".env.local"
    logger.info(f"Looking for .env.local file at: {env_path}")

    if env_path.exists():
        logger.info(f".env.local file found at {env_path}")
        load_dotenv(dotenv_path=env_path)
        if os.getenv("GEMINI_API_KEY"):
            logger.info(f"API key loaded from .env.local: {os.getenv('GEMINI_API_KEY')[:10]}...")
        else:
            logger.error("GEMINI_API_KEY not found in .env.local file")
    else:
        logger.error(f".env.local file not found at {env_path}")


def get_gemini_api_key() -> str:
    """Get Gemini API key from environment."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured in backend/.env.local file or environment")
    return api_key


# Few-shot examples for SQL generation
FEW_SHOT_EXAMPLES = [
    {
        "user_name": "John Doe",
        "user_email": "john.doe@example.com",
        "q": "How many patients are there?",
        "a": "SELECT COUNT(*) FROM ASRIT_PATIENT;",
    },
    {
        "user_name": "Jane Smith",
        "user_email": "jane.smith@example.com",
        "q": "Show me all patient details for patients older than 18",
        "a": "SELECT * FROM ASRIT_PATIENT WHERE AGE > 18;",
    },
    {
        "user_name": "Bob Johnson",
        "user_email": "bob.johnson@example.com",
        "q": "Get patient ID and name for female patients",
        "a": "SELECT PATIENT_ID, FIRST_NAME, MIDDLE_NAME, LAST_NAME FROM ASRIT_PATIENT WHERE GENDER = 'F';",
    },
    {
        "user_name": "Alice Brown",
        "user_email": "alice.brown@example.com",
        "q": "Show me all patient details including name, age, gender, address, and contact information for patients older than 18, top 10 rows",
        "a": "SELECT * FROM ASRIT_PATIENT WHERE AGE > 18 FETCH FIRST 10 ROWS ONLY;",
    },
    {
        "user_name": "Charlie Wilson",
        "user_email": "charlie.wilson@example.com",
        "q": "Get all patient information",
        "a": "SELECT * FROM ASRIT_PATIENT;",
    },
]


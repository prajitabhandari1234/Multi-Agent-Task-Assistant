
import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables.
load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

# Timeout in seconds.
GEMINI_TIMEOUT_SECONDS = 30

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from the environment.")

# Google GenAI SDK accepts HTTP timeout in milliseconds.
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        timeout=GEMINI_TIMEOUT_SECONDS * 1000,
    ),
)


def generate_response(prompt: str) -> str:
    """
    Send a prompt to Gemini with timeout handling,
    output validation, and error logging.
    """

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Gemini prompt must be a non-empty string.")

    try:
        logger.info("Sending request to Gemini.")

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt.strip(),
        )

        response_text = getattr(response, "text", None)

        if not isinstance(response_text, str) or not response_text.strip():
            raise ValueError("Gemini returned an empty or invalid response.")

        logger.info("Gemini response received successfully.")

        return response_text.strip()

    except Exception as error:
        logger.exception("Gemini request failed.")

        raise RuntimeError(
            f"Gemini request failed: {error}"
        ) from error


def get_langchain_model():
    """
    Create a LangChain Gemini model for the
    existing single-agent task assistant.
    """

    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=0,
        google_api_key=GEMINI_API_KEY,
        timeout=GEMINI_TIMEOUT_SECONDS,
    )

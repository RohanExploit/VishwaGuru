import json
import os
import google.generativeai as genai
from typing import Optional, Callable, Any
import warnings
from functools import lru_cache
from typing import Optional
import logging

import google.generativeai as genai
from async_lru import alru_cache
import asyncio
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Suppress deprecation warnings from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

logger = logging.getLogger(__name__)

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    # Allow dummy key for testing/building if not strictly required at startup
    api_key = "dummy"
    if os.environ.get("ENVIRONMENT") == "production":
         logger.warning("GEMINI_API_KEY not set in production environment!")

genai.configure(api_key=api_key)

RESPONSIBILITY_MAP_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "responsibility_map.json")

async def retry_with_exponential_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    *args,
    **kwargs
) -> Any:
    """
    Retry an async function with exponential backoff.

    Args:
        func: The async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Factor to multiply delay by each retry
        *args, **kwargs: Arguments to pass to the function

    Returns:
        The result of the function call

    Raises:
        The last exception encountered if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if attempt == max_retries:
                # Last attempt failed, re-raise the exception
                logger.error(f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}")
                raise e

            # Calculate delay with exponential backoff
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)

            logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {delay:.1f}s")
            await asyncio.sleep(delay)

    # This should never be reached, but just in case
    raise last_exception


@lru_cache(maxsize=1)
def _load_responsibility_map() -> dict:
    """Load responsibility map for authority tagging."""
    try:
        with open(RESPONSIBILITY_MAP_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def build_x_post(issue_description: str, category: str) -> str:
    """
    Build an X.com (Twitter) post tagging the relevant authority when available.
    """
    responsibility_map = _load_responsibility_map()
    category_key = str(category).lower().replace(" ", "_")
    authority_info = responsibility_map.get(category_key, {})
    handle = authority_info.get("twitter")

    base_message = f"Reporting a {category} issue: {issue_description[:200]}"
    if handle:
        return f"{base_message} Tagging {handle} for prompt action. #CivicIssue #VishwaGuru"
    return f"{base_message} #CivicIssue #VishwaGuru"


async def generate_action_plan(issue_description: str, category: str, language: str = 'en', image_path: Optional[str] = None) -> dict:
    """
    Generates an action plan (WhatsApp message, Email draft) using Gemini with retry logic.
    """
    # Generate X post content first using the logic
    x_post_text = build_x_post(issue_description, category)

    # Fallback response for when AI is unavailable
    fallback_response = {
        "whatsapp": f"Hello, I would like to report a {category} issue: {issue_description}",
        "email_subject": f"Complaint regarding {category}",
        "email_body": f"Respected Authority,\n\nI am writing to bring to your attention a {category} issue: {issue_description}.\n\nPlease take necessary action.\n\nSincerely,\nCitizen",
        "x_post": x_post_text
    }

    async def _generate_with_gemini() -> dict:
        """Inner function to generate action plan with Gemini"""
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        You are a civic action assistant. A user has reported a civic issue.
        Category: {category}
        Description: {issue_description}

        Please generate the following messages in {language} language:
        1. A concise WhatsApp message (max 200 chars) that can be sent to authorities.
        2. A formal but firm email subject.
        3. A formal email body (max 150 words) addressed to the relevant authority (e.g., Municipal Commissioner, Police, etc. based on category).
        4. A concise X.com post text (max 240 chars). If provided, prefer this authority handle for tagging: {x_post_text}

        Return the response in strictly valid JSON format with keys: "whatsapp", "email_subject", "email_body", "x_post".
        Do not use markdown code blocks. Just the raw JSON string.
        """

        response = await model.generate_content_async(prompt)
        text_response = response.text.strip()

        # Cleanup if markdown code blocks are returned
        if "```json" in text_response:
             text_response = text_response.split("```json")[1].split("```")[0]
        elif "```" in text_response:
             text_response = text_response.split("```")[1].split("```")[0]

        text_response = text_response.strip()

        try:
            plan = json.loads(text_response)
        except json.JSONDecodeError:
            # Try to fix common JSON errors if possible, or fallback
            logger.error(f"Gemini returned invalid JSON: {text_response}")
            raise Exception("Invalid JSON from AI")

        if "x_post" not in plan or not plan.get("x_post"):
            plan["x_post"] = x_post_text
        return plan

    try:
        return await retry_with_exponential_backoff(_generate_with_gemini, max_retries=3)
    except Exception as e:
        logger.error(f"Gemini action plan generation failed after retries: {e}")
        return fallback_response

@alru_cache(maxsize=100)
async def chat_with_civic_assistant(query: str) -> str:
    """
    Chat with the civic assistant using Gemini with retry logic.
    """
    async def _chat_with_gemini() -> str:
        """Inner function to chat with Gemini"""
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        You are VishwaGuru, a helpful civic assistant for Indian citizens.
        User Query: {query}

        Answer the user's question about civic issues, government services, or local administration.
        If they ask about specific MLAs, tell them to use the "Find My MLA" feature.
        Keep answers concise and helpful.
        """

        response = await model.generate_content_async(prompt)
        return response.text.strip()

    try:
        return await retry_with_exponential_backoff(_chat_with_gemini, max_retries=2)
    except Exception as e:
        logger.error(f"Gemini chat failed after retries: {e}")
        return "I encountered an error processing your request. Please try again later."

import json
import os
import google.generativeai as genai
from typing import Optional, List, Dict, Any
import warnings
from functools import lru_cache
from typing import Optional
import logging

import google.generativeai as genai
from async_lru import alru_cache
import json
import PIL.Image

# Suppress deprecation warnings from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="google.generativeai")

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    # Allow dummy key for testing/building if not strictly required at startup
    api_key = "dummy"
    if os.environ.get("ENVIRONMENT") == "production":
         logger.warning("GEMINI_API_KEY not set in production environment!")

def _get_fallback_action_plan(issue_description: str, category: str) -> dict:
    """Generate fallback action plan when AI is unavailable."""
    return {
        "whatsapp": f"Hello, I would like to report a {category} issue: {issue_description}",
        "email_subject": f"Complaint regarding {category}",
        "email_body": f"Respected Authority,\n\nI am writing to bring to your attention a {category} issue: {issue_description}.\n\nPlease take necessary action.\n\nSincerely,\nCitizen"
    }


@exponential_backoff_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
async def _generate_action_plan_with_retry(issue_description: str, category: str) -> dict:
    """
    Internal function that generates action plan with retry logic.
    Raises exception on failure to allow retry decorator to work.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are a civic action assistant. A user has reported a civic issue.
    Category: {category}
    Description: {issue_description}

    Please generate:
    1. A concise WhatsApp message (max 200 chars) that can be sent to authorities.
    2. A formal but firm email subject.
    3. A formal email body (max 150 words) addressed to the relevant authority (e.g., Municipal Commissioner, Police, etc. based on category).

    Return the response in strictly valid JSON format with keys: "whatsapp", "email_subject", "email_body".
    Do not use markdown code blocks. Just the raw JSON string.
    """

    response = await model.generate_content_async(prompt)
    text_response = response.text.strip()

    # Cleanup if markdown code blocks are returned
    if text_response.startswith("```json"):
        text_response = text_response[7:-3]
    elif text_response.startswith("```"):
        text_response = text_response[3:-3]

    return json.loads(text_response)


async def generate_action_plan(issue_description: str, category: str, image_path: Optional[str] = None) -> dict:
    """
    Generates an action plan (WhatsApp message, Email draft) using Gemini.
    Includes retry logic with exponential backoff for transient failures.
    """
    if not api_key:
        logger.warning("No API key configured, using fallback action plan")
        return _get_fallback_action_plan(issue_description, category)

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
                raise AIServiceException(
                    f"AI service operation failed after {max_retries + 1} attempts",
                    service="Gemini",
                    details={"function": func.__name__, "error": str(e)}
                ) from e

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
        # Use Gemini 1.5 Flash for faster response times
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        You are a civic action assistant. A user has reported a civic issue.
        Category: {category}
        Description: {issue_description}

        Please generate:
        1. A concise WhatsApp message (max 200 chars) that can be sent to authorities.
        2. A formal but firm email subject.
        3. A formal email body (max 150 words) addressed to the relevant authority (e.g., Municipal Commissioner, Police, etc. based on category).

        Return the response in strictly valid JSON format with keys: "whatsapp", "email_subject", "email_body".
        Do not use markdown code blocks. Just the raw JSON string.
        """

        # Generate content without any tools (no Google Search, no internet retrieval)
        # Explicitly set tools=None to ensure no search/grounding features are used
        response = await client.aio.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                tools=None  # Explicitly disable all tools including Google Search
            )
        )
        text_response = response.text.strip()

        # Cleanup if markdown code blocks are returned
        if text_response.startswith("```json"):
            text_response = text_response[7:-3]
        elif text_response.startswith("```"):
            text_response = text_response[3:-3]

        return json.loads(text_response)

    except Exception as e:
        logger.error(f"Gemini Error after all retries: {e}", exc_info=True)
        # Return fallback after all retries exhausted
        return _get_fallback_action_plan(issue_description, category)

@exponential_backoff_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
async def _chat_with_civic_assistant_with_retry(query: str) -> str:
    """
    Internal function that handles chat with retry logic.
    Raises exception on failure to allow retry decorator to work.
    """
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


@alru_cache(maxsize=100)
async def chat_with_civic_assistant(query: str, history: List[dict] = []) -> str:
    """
    Chat with the civic assistant.
    Includes retry logic with exponential backoff for transient failures.
    """
    if not api_key:
        logger.warning("No API key configured, chat assistant offline")
        return "I am currently offline. Please try again later."

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Construct context from history
        history_context = ""
        if history:
            history_context = "Previous conversation:\n"
            for msg in history[-5:]: # Keep last 5 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_context += f"{role}: {content}\n"

        prompt = f"""
        You are VishwaGuru, a helpful civic assistant for Indian citizens.
        {history_context}
        User Query: {query}

        Answer the user's question about civic issues, government services, or local administration.
        If they ask about specific MLAs, tell them to use the "Find My MLA" feature.
        Keep answers concise and helpful.
        """

        # Generate content without any tools (no Google Search, no internet retrieval)
        # Explicitly set tools=None to ensure no search/grounding features are used
        response = await client.aio.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                tools=None  # Explicitly disable all tools including Google Search
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini Chat Error: {e}")
        return "I encountered an error processing your request."

async def analyze_issue_image(image_path: str) -> Dict[str, Any]:
    """
    Analyzes an image to detect the civic issue, category, and severity.
    """
    if not api_key:
        return {
            "description": "AI analysis unavailable",
            "category": "Uncategorized",
            "severity": "Unknown"
        }

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        if not os.path.exists(image_path):
             return {"error": "Image file not found"}

        img = PIL.Image.open(image_path)

        prompt = """
        Analyze this image of a civic issue.
        Identify:
        1. A short description of the issue.
        2. The category (e.g., Pothole, Garbage, Flooding, Vandalism, Street Light, etc.).
        3. The severity (Low, Medium, High).

        Return valid JSON with keys: "description", "category", "severity".
        """

        response = await model.generate_content_async([prompt, img])
        text_response = response.text.strip()

        if text_response.startswith("```json"):
            text_response = text_response[7:-3]
        elif text_response.startswith("```"):
            text_response = text_response[3:-3]

        return json.loads(text_response)

    except Exception as e:
        print(f"Gemini Image Analysis Error: {e}")
        return {
            "description": "Could not analyze image",
            "category": "Unknown",
            "severity": "Unknown"
        }

async def analyze_issue_with_ai(description: str, image_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes an issue description and optional image.
    """
    if not api_key:
        return {
             "category": "General",
             "severity": "Medium",
             "authority": "Local Municipal Corporation",
             "action_plan": "Report to local ward office."
        }

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        content = []
        prompt_text = f"""
        Analyze this civic issue report.
        Description: {description}

        Determine:
        1. The most appropriate Category.
        2. Severity Level (Low, Medium, High).
        3. Responsible Authority in India (e.g., BMC, Police, MSEB, etc.).
        4. A recommended Action Plan (short sentence).

        Return valid JSON with keys: "category", "severity", "authority", "action_plan".
        """
        content.append(prompt_text)

        if image_path and os.path.exists(image_path):
            img = PIL.Image.open(image_path)
            content.append(img)

        response = await model.generate_content_async(content)
        text_response = response.text.strip()

        if text_response.startswith("```json"):
            text_response = text_response[7:-3]
        elif text_response.startswith("```"):
            text_response = text_response[3:-3]

        return json.loads(text_response)

    except Exception as e:
        print(f"Gemini Analysis Error: {e}")
        return {
             "category": "General",
             "severity": "Medium",
             "authority": "Local Authority",
             "action_plan": "Please visit the nearest municipal office."
        }

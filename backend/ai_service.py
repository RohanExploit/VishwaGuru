import json
import os
import base64
import asyncio
import logging
import warnings
from typing import Optional, List, Dict, Any
from functools import lru_cache

import httpx

from backend.retry_utils import exponential_backoff_retry
from backend.exceptions import AIServiceException

# Configure logging
logger = logging.getLogger(__name__)

# ── API Configuration ──────────────────────────────────────────────────────────
# Priority: NVIDIA_API_KEY > GEMINI_API_KEY > fallback (no AI)
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# NVIDIA NIM model names
NVIDIA_TEXT_MODEL = "meta/llama-3.1-70b-instruct"
NVIDIA_VISION_MODEL = "meta/llama-3.2-90b-vision-instruct"

if NVIDIA_API_KEY:
    API_MODE = "nvidia"
    API_KEY = NVIDIA_API_KEY
    API_BASE = "https://integrate.api.nvidia.com/v1"
    MODEL_NAME = NVIDIA_TEXT_MODEL
    VISION_MODEL = NVIDIA_VISION_MODEL
    logger.info(
        f"AI Service: Using NVIDIA NIM — "
        f"Text: {NVIDIA_TEXT_MODEL}, Vision: {NVIDIA_VISION_MODEL}"
    )
elif GEMINI_API_KEY:
    API_MODE = "gemini"
    API_KEY = GEMINI_API_KEY
    API_BASE = None
    MODEL_NAME = "gemini-1.5-flash"
    VISION_MODEL = "gemini-1.5-flash"
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="google.generativeai")
    except ImportError:
        logger.warning("google-generativeai not installed, falling back to no-AI mode")
        API_MODE = "none"
        API_KEY = None
    logger.info("AI Service: Using Google Gemini API (gemini-1.5-flash)")
else:
    API_MODE = "none"
    API_KEY = None
    API_BASE = None
    MODEL_NAME = None
    VISION_MODEL = None
    if os.environ.get("ENVIRONMENT") == "production":
        logger.warning("No AI API key set in production! Set NVIDIA_API_KEY or GEMINI_API_KEY.")
    else:
        logger.info("AI Service: No API key configured — running in fallback mode")


RESPONSIBILITY_MAP_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "responsibility_map.json"
)

# Max image size (pixels) before we resize to save bandwidth / token cost
_MAX_IMAGE_DIM = 1024


@lru_cache(maxsize=1)
def _load_responsibility_map() -> dict:
    """Load responsibility map for authority tagging."""
    try:
        with open(RESPONSIBILITY_MAP_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def build_x_post(issue_description: str, category: str) -> str:
    """Build an X.com (Twitter) post tagging the relevant authority when available."""
    responsibility_map = _load_responsibility_map()
    category_key = str(category).lower().replace(" ", "_")
    authority_info = responsibility_map.get(category_key, {})
    handle = authority_info.get("twitter")

    base_message = f"Reporting a {category} issue: {issue_description[:200]}"
    if handle:
        return f"{base_message} Tagging {handle} for prompt action. #CivicIssue #VishwaGuru"
    return f"{base_message} #CivicIssue #VishwaGuru"


def _get_fallback_action_plan(issue_description: str, category: str) -> dict:
    """Generate fallback action plan when AI is unavailable."""
    return {
        "whatsapp": f"Hello, I would like to report a {category} issue: {issue_description[:150]}",
        "email_subject": f"Complaint regarding {category}",
        "email_body": (
            f"Respected Authority,\n\nI am writing to bring to your attention "
            f"a {category} issue: {issue_description}.\n\nPlease take necessary "
            f"action.\n\nSincerely,\nCitizen"
        ),
        "x_post": build_x_post(issue_description, category),
    }


# ── Image helpers ──────────────────────────────────────────────────────────────

def _encode_image_to_base64(image_path: str) -> tuple[str, str]:
    """
    Read an image from disk, optionally resize to save bandwidth, and
    return (base64_string, mime_type).
    """
    import PIL.Image
    import io

    img = PIL.Image.open(image_path)
    # Convert RGBA → RGB (JPEG doesn't support alpha)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")

    # Resize if too large
    if max(img.size) > _MAX_IMAGE_DIM:
        img.thumbnail((_MAX_IMAGE_DIM, _MAX_IMAGE_DIM), PIL.Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return b64, "image/jpeg"


def _encode_pil_image_to_base64(pil_image) -> tuple[str, str]:
    """Encode a PIL.Image object to base64 JPEG."""
    import io

    img = pil_image
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")
    if max(img.size) > _MAX_IMAGE_DIM:
        img.thumbnail((_MAX_IMAGE_DIM, _MAX_IMAGE_DIM))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return b64, "image/jpeg"


# ── NVIDIA NIM helpers ─────────────────────────────────────────────────────────

async def _nvidia_chat_completion(prompt: str, max_tokens: int = 1024) -> str:
    """Call NVIDIA NIM OpenAI-compatible chat completions (text-only)."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "top_p": 0.9,
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


async def _nvidia_vision_completion(
    prompt: str,
    image_b64: str,
    mime_type: str = "image/jpeg",
    max_tokens: int = 1024,
) -> str:
    """
    Call NVIDIA NIM vision model with an image (base64-encoded).
    Uses the OpenAI-compatible multimodal message format.
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_b64}",
                        },
                    },
                ],
            }
        ],
        "temperature": 0.3,
        "top_p": 0.9,
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


def _clean_json_response(text: str) -> str:
    """Strip markdown code fences from an LLM JSON response."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


# ── Action Plan ────────────────────────────────────────────────────────────────

@exponential_backoff_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
async def _generate_action_plan_with_retry(
    issue_description: str, category: str, language: str = "en"
) -> dict:
    """Generate action plan via the configured AI backend (with retry)."""
    prompt = f"""You are a civic action assistant. A user has reported a civic issue.
Category: {category}
Description: {issue_description}

Please generate the following messages in {language} language:
1. A concise WhatsApp message (max 200 chars) that can be sent to authorities.
2. A formal firm email subject.
3. A formal email body (max 150 words) addressed to the relevant authority (e.g., Municipal Commissioner, Police, etc. based on category).
4. A concise X.com post text (max 240 chars).

Return the response in strictly valid JSON format with keys: "whatsapp", "email_subject", "email_body", "x_post".
Do not use markdown code blocks. Just the raw JSON string."""

    if API_MODE == "nvidia":
        text_response = await _nvidia_chat_completion(prompt)
    elif API_MODE == "gemini":
        import google.generativeai as genai

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = await model.generate_content_async(prompt)
        text_response = response.text.strip()
    else:
        raise AIServiceException("No AI backend configured")

    text_response = _clean_json_response(text_response)
    return json.loads(text_response)


async def generate_action_plan(
    issue_description: str,
    category: str,
    *args,
    **kwargs,
) -> dict:
    """Generates an action plan (WhatsApp, Email, X post) using AI with retry."""
    if API_MODE == "none":
        logger.warning("No API key configured, using fallback action plan")
        return _get_fallback_action_plan(issue_description, category)

    language = "en"
    image_path = None

    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, str) and len(arg) == 2:
            language = arg
        else:
            image_path = arg
    elif len(args) >= 2:
        language = args[0]
        image_path = args[1]

    if "language" in kwargs:
        language = kwargs["language"]
    if "image_path" in kwargs:
        image_path = kwargs["image_path"]

    try:
        plan = await _generate_action_plan_with_retry(
            issue_description, category, language
        )
        if "x_post" not in plan or not plan.get("x_post"):
            plan["x_post"] = build_x_post(issue_description, category)
        return plan
    except Exception as e:
        logger.error(f"AI action plan generation failed after retries: {e}")
        return _get_fallback_action_plan(issue_description, category)


# ── Chat Assistant ─────────────────────────────────────────────────────────────

@exponential_backoff_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
async def _chat_with_civic_assistant_with_retry(
    query: str, history_context: str = ""
) -> str:
    prompt = f"""You are VishwaGuru, a helpful civic assistant for Indian citizens.
{history_context}
User Query: {query}

Answer the user's question about civic issues, government services, or local administration.
If they ask about specific MLAs, tell them to use the "Find My MLA" feature.
Keep answers concise and helpful."""

    if API_MODE == "nvidia":
        return await _nvidia_chat_completion(prompt)
    elif API_MODE == "gemini":
        import google.generativeai as genai

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    else:
        raise AIServiceException("No AI backend configured")


async def chat_with_civic_assistant(
    query: str, history: Optional[List[dict]] = None
) -> str:
    """Chat with the civic assistant. Includes retry logic with exponential backoff."""
    if API_MODE == "none":
        logger.warning("No API key configured, chat assistant offline")
        return "I am currently offline. Please try again later."

    history_context = ""
    if history:
        history_context = "Previous conversation:\n"
        for msg in history[-5:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_context += f"{role}: {content}\n"

    try:
        return await _chat_with_civic_assistant_with_retry(query, history_context)
    except Exception as e:
        logger.error(f"AI Chat Error after all retries: {e}", exc_info=True)
        return "I encountered an error processing your request. Please try again later."


# ── Image Analysis (NVIDIA Vision) ────────────────────────────────────────────

_IMAGE_ANALYSIS_PROMPT = """Analyze this image of a civic issue in India.
Identify:
1. A short description of the issue (max 50 words).
2. The category — pick ONE from: Pothole, Garbage, Flooding, Vandalism, Street Light, Broken Infrastructure, Illegal Parking, Fire, Stray Animal, Blocked Road, Tree Hazard, Other.
3. The severity — pick ONE from: Low, Medium, High.

Return valid JSON with keys: "description", "category", "severity".
Do not use markdown code blocks. Just the raw JSON string."""

_ISSUE_ANALYSIS_PROMPT = """Analyze this civic issue report.
Description: {description}

Determine:
1. The most appropriate Category.
2. Severity Level (Low, Medium, High).
3. Responsible Authority in India (e.g., BMC, Police, MSEB, etc.).
4. A recommended Action Plan (short sentence).

Return valid JSON with keys: "category", "severity", "authority", "action_plan".
Do not use markdown code blocks. Just the raw JSON string."""

_ISSUE_ANALYSIS_WITH_IMAGE_PROMPT = """Analyze this civic issue report. An image of the issue is attached.
Description: {description}

Using BOTH the description and the image, determine:
1. The most appropriate Category.
2. Severity Level (Low, Medium, High).
3. Responsible Authority in India (e.g., BMC, Police, MSEB, etc.).
4. A recommended Action Plan (short sentence).

Return valid JSON with keys: "category", "severity", "authority", "action_plan".
Do not use markdown code blocks. Just the raw JSON string."""


@exponential_backoff_retry(max_retries=2, base_delay=2.0, max_delay=15.0)
async def analyze_issue_image(image_path: str) -> Dict[str, Any]:
    """
    Analyze an uploaded image using NVIDIA NIM vision model
    (meta/llama-3.2-90b-vision-instruct) or Gemini multimodal.
    Returns: {"description", "category", "severity"}
    """
    if API_MODE == "none":
        return {
            "description": "AI analysis unavailable",
            "category": "Uncategorized",
            "severity": "Unknown",
        }

    if not os.path.exists(image_path):
        return {"error": "Image file not found"}

    try:
        if API_MODE == "nvidia":
            # ── NVIDIA NIM Vision ──────────────────────────────────────────
            image_b64, mime = _encode_image_to_base64(image_path)
            text_response = await _nvidia_vision_completion(
                prompt=_IMAGE_ANALYSIS_PROMPT,
                image_b64=image_b64,
                mime_type=mime,
                max_tokens=512,
            )
            logger.info("Image analyzed via NVIDIA NIM Vision model")

        elif API_MODE == "gemini":
            # ── Gemini multimodal ──────────────────────────────────────────
            import PIL.Image
            import google.generativeai as genai

            img = PIL.Image.open(image_path)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = await model.generate_content_async(
                [_IMAGE_ANALYSIS_PROMPT, img]
            )
            text_response = response.text.strip()
        else:
            raise AIServiceException("No AI backend configured")

        text_response = _clean_json_response(text_response)
        return json.loads(text_response)

    except json.JSONDecodeError as e:
        logger.error(f"Vision model returned non-JSON: {e}")
        return {
            "description": "AI returned unparseable response",
            "category": "Unknown",
            "severity": "Unknown",
        }
    except Exception as e:
        logger.error(f"Image Analysis Error: {e}", exc_info=True)
        return {
            "description": "Could not analyze image",
            "category": "Unknown",
            "severity": "Unknown",
        }


@exponential_backoff_retry(max_retries=2, base_delay=2.0, max_delay=15.0)
async def analyze_issue_with_ai(
    description: str, image_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a civic issue description with optional image.
    Uses NVIDIA Vision model when image is provided.
    Returns: {"category", "severity", "authority", "action_plan"}
    """
    if API_MODE == "none":
        return {
            "category": "General",
            "severity": "Medium",
            "authority": "Local Municipal Corporation",
            "action_plan": "Report to local ward office.",
        }

    try:
        has_image = image_path and os.path.exists(image_path)

        if API_MODE == "nvidia":
            if has_image:
                # ── Vision model for image + text ──────────────────────────
                image_b64, mime = _encode_image_to_base64(image_path)
                prompt = _ISSUE_ANALYSIS_WITH_IMAGE_PROMPT.format(
                    description=description
                )
                text_response = await _nvidia_vision_completion(
                    prompt=prompt,
                    image_b64=image_b64,
                    mime_type=mime,
                    max_tokens=512,
                )
                logger.info("Issue analyzed with NVIDIA Vision (image + text)")
            else:
                # ── Text-only model ────────────────────────────────────────
                prompt = _ISSUE_ANALYSIS_PROMPT.format(description=description)
                text_response = await _nvidia_chat_completion(prompt)

        elif API_MODE == "gemini":
            import google.generativeai as genai

            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = _ISSUE_ANALYSIS_PROMPT.format(description=description)
            content = [prompt]
            if has_image:
                import PIL.Image

                img = PIL.Image.open(image_path)
                content.append(img)
            response = await model.generate_content_async(content)
            text_response = response.text.strip()
        else:
            raise AIServiceException("No AI backend configured")

        text_response = _clean_json_response(text_response)
        return json.loads(text_response)

    except json.JSONDecodeError as e:
        logger.error(f"AI returned non-JSON for issue analysis: {e}")
        return {
            "category": "General",
            "severity": "Medium",
            "authority": "Local Authority",
            "action_plan": "Please visit the nearest municipal office.",
        }
    except Exception as e:
        logger.error(f"AI Analysis Error: {e}", exc_info=True)
        return {
            "category": "General",
            "severity": "Medium",
            "authority": "Local Authority",
            "action_plan": "Please visit the nearest municipal office.",
        }

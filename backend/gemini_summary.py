"""
MLA Summary Service for Maharashtra MLA Information

Uses NVIDIA NIM (primary) or Gemini AI (fallback) to generate human-readable
summaries about MLAs and their roles.
Includes retry logic with exponential backoff for handling transient failures.
"""
import os
import logging
from typing import Optional

import httpx

from backend.retry_utils import exponential_backoff_retry

# Configure logging
logger = logging.getLogger(__name__)

# ── API Configuration (mirrors ai_service.py) ─────────────────────────────────
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if NVIDIA_API_KEY:
    _API_MODE = "nvidia"
    _API_KEY = NVIDIA_API_KEY
    _API_BASE = "https://integrate.api.nvidia.com/v1"
    _MODEL_NAME = "meta/llama-3.1-70b-instruct"
elif GEMINI_API_KEY:
    _API_MODE = "gemini"
    _API_KEY = GEMINI_API_KEY
    _API_BASE = None
    _MODEL_NAME = "gemini-1.5-flash"
    try:
        import google.generativeai as genai
        import warnings
        genai.configure(api_key=GEMINI_API_KEY)
        warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
    except ImportError:
        _API_MODE = "none"
        _API_KEY = None
else:
    _API_MODE = "none"
    _API_KEY = None
    _API_BASE = None
    _MODEL_NAME = None


def _get_fallback_summary(mla_name: str, assembly_constituency: str, district: str) -> str:
    """Generate a fallback summary when AI is unavailable or fails."""
    return (
        f"{mla_name} represents the {assembly_constituency} assembly constituency "
        f"in {district} district, Maharashtra. MLAs handle local issues such as "
        f"infrastructure, public services, and constituent welfare."
    )


async def _nvidia_chat(prompt: str) -> str:
    """Call NVIDIA NIM chat completions."""
    headers = {
        "Authorization": f"Bearer {_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "top_p": 0.9,
        "max_tokens": 512,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{_API_BASE}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


@exponential_backoff_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
async def _generate_mla_summary_with_retry(
    district: str,
    assembly_constituency: str,
    mla_name: str,
    issue_category: Optional[str] = None
) -> str:
    """Internal function that generates MLA summary with retry logic."""
    issue_context = f" particularly regarding {issue_category} issues" if issue_category else ""

    prompt = f"""You are helping an Indian citizen understand who represents them.
In one short paragraph (max 100 words), explain that the MLA {mla_name} represents
the assembly constituency {assembly_constituency} in district {district}, state Maharashtra{issue_context},
and what type of local issues they typically handle.

Do not hallucinate phone numbers or emails; only talk about roles and responsibilities.
Keep it factual, helpful, and encouraging for civic engagement."""

    if _API_MODE == "nvidia":
        return await _nvidia_chat(prompt)
    elif _API_MODE == "gemini":
        import google.generativeai as genai
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    else:
        raise RuntimeError("No AI backend configured")


async def generate_mla_summary(
    district: str,
    assembly_constituency: str,
    mla_name: str,
    issue_category: Optional[str] = None
) -> str:
    """
    Generate a human-readable summary about an MLA using AI.
    Includes retry logic with exponential backoff for transient failures.
    """
    if _API_MODE == "none":
        logger.warning("No API key configured, using fallback MLA summary")
        return _get_fallback_summary(mla_name, assembly_constituency, district)

    try:
        return await _generate_mla_summary_with_retry(
            district, assembly_constituency, mla_name, issue_category
        )
    except Exception as e:
        logger.error(f"AI Summary Error after all retries: {e}", exc_info=True)
        return _get_fallback_summary(mla_name, assembly_constituency, district)

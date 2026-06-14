"""
Gemini Summary Service for Maharashtra MLA Information

Uses Gemini AI to generate human-readable summaries about MLAs and their roles.
"""
import os
import google.generativeai as genai
from typing import Dict, Optional, Callable, Any
import warnings
import time
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from backend.ai_service import retry_with_exponential_backoff

# Suppress deprecation warnings from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

logger = logging.getLogger(__name__)

# Manual async cache to replace async_lru (removes heavy dependency for deployment)
# Structure: {cache_key: (summary_text, expiry_timestamp)}
_summary_cache: Dict[str, tuple[str, datetime]] = {}

# Configure Gemini (mandatory environment variable)
api_key = os.environ.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    # Gemini disabled (mock/local mode)
    genai = None

def _get_fallback_summary(mla_name: str, assembly_constituency: str, district: str) -> str:
    """
    Generate a fallback summary when Gemini is unavailable or fails.
    
    Args:
        mla_name: Name of the MLA
        assembly_constituency: Assembly constituency name
        district: District name
        
    Returns:
        A simple fallback description
    """
    return (
        f"{mla_name} represents the {assembly_constituency} assembly constituency "
        f"in {district} district, Maharashtra. MLAs handle local issues such as "
        f"infrastructure, public services, and constituent welfare."
    )


# Simple cache to avoid async-lru dependency
_summary_cache = {}
SUMMARY_CACHE_TTL = 86400  # 24 hours

async def generate_mla_summary(
    district: str,
    assembly_constituency: str,
    mla_name: str,
    issue_category: Optional[str] = None
) -> str:
    """
    Generate a human-readable summary about an MLA using Gemini with retry logic.
    Optimized: Uses a simple manual cache to remove async-lru dependency.

    Args:
        district: District name
        assembly_constituency: Assembly constituency name
        mla_name: Name of the MLA
        issue_category: Optional category of issue for context

    Returns:
        A short paragraph describing the MLA's role and responsibilities
    """
    cache_key = f"{district}_{assembly_constituency}_{mla_name}_{issue_category}"
    current_time = time.time()

    if cache_key in _summary_cache:
        val, ts = _summary_cache[cache_key]
        if current_time - ts < SUMMARY_CACHE_TTL:
            return val

    async def _generate_mla_summary_with_gemini() -> str:
        """Inner function to generate MLA summary with Gemini"""
        model = genai.GenerativeModel('gemini-1.5-flash')

        issue_context = f" particularly regarding {issue_category} issues" if issue_category else ""

        prompt = f"""
        You are helping an Indian citizen understand who represents them.
        In one short paragraph (max 100 words), explain that the MLA {mla_name} represents
        the assembly constituency {assembly_constituency} in district {district}, state Maharashtra{issue_context},
        and what type of local issues they typically handle.

        Do not hallucinate phone numbers or emails; only talk about roles and responsibilities.
        Keep it factual, helpful, and encouraging for civic engagement.
        """

        response = await model.generate_content_async(prompt)
        return response.text.strip()

    try:
        summary = await retry_with_exponential_backoff(_generate_mla_summary_with_gemini, max_retries=2)
        _summary_cache[cache_key] = (summary, current_time)
        return summary
    except Exception as e:
        logger.error(f"Gemini MLA summary generation failed after retries: {e}")
        # Fallback to simple description
        return _get_fallback_summary(mla_name, assembly_constituency, district)

"""
Gemini Summary Service for Maharashtra MLA Information

Uses Gemini AI to generate human-readable summaries about MLAs and their roles.
Includes retry logic with exponential backoff for handling transient failures.
"""
import os
import google.generativeai as genai
from typing import Dict, Optional, Callable, Any
import warnings
from async_lru import alru_cache
from retry_utils import exponential_backoff_retry
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Suppress deprecation warnings from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

logger = logging.getLogger(__name__)

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


@exponential_backoff_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
async def _generate_mla_summary_with_retry(
    district: str,
    assembly_constituency: str,
    mla_name: str,
    issue_category: Optional[str] = None
) -> str:
    """
    Internal function that generates MLA summary with retry logic.
    Raises exception on failure to allow retry decorator to work.
    """
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


@alru_cache(maxsize=100)
async def generate_mla_summary(
    district: str,
    assembly_constituency: str,
    mla_name: str,
    issue_category: Optional[str] = None
) -> str:
    """
    Generate a human-readable summary about an MLA using Gemini.
    Includes retry logic with exponential backoff for transient failures.
    
    Args:
        district: District name
        assembly_constituency: Assembly constituency name
        mla_name: Name of the MLA
        issue_category: Optional category of issue for context

    Returns:
        A short paragraph describing the MLA's role and responsibilities
    """
    if not api_key:
        logger.warning("No API key configured, using fallback MLA summary")
        return _get_fallback_summary(mla_name, assembly_constituency, district)
    
    try:
        issue_context = f" particularly regarding {issue_category} issues" if issue_category else ""
        
        prompt = f"""
        You are helping an Indian citizen understand who represents them. 
        In one short paragraph (max 100 words), explain that the MLA {mla_name} represents 
        the assembly constituency {assembly_constituency} in district {district}, state Maharashtra{issue_context}, 
        and what type of local issues they typically handle.
        
        Do not hallucinate phone numbers or emails; only talk about roles and responsibilities.
        Keep it factual, helpful, and encouraging for civic engagement.
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
        logger.error(f"Gemini Summary Error after all retries: {e}", exc_info=True)
        # Return fallback after all retries exhausted
        return _get_fallback_summary(mla_name, assembly_constituency, district)

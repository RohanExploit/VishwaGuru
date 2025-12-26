"""
Gemini Summary Service for Maharashtra MLA Information

Uses Gemini AI to generate human-readable summaries about MLAs and their roles.
"""
import os
from google import genai
from typing import Dict, Optional
from async_lru import alru_cache

# Configure Gemini (reuses existing configuration)
# Use provided key as fallback if env var is missing
api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyB8_i3tbDE3GmX4CsQ8G3mD3pB2WrHi5C8")
client = None
if api_key:
    client = genai.Client(api_key=api_key)


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


@alru_cache(maxsize=100)
async def generate_mla_summary(
    district: str,
    assembly_constituency: str,
    mla_name: str,
    issue_category: Optional[str] = None
) -> str:
    """
    Generate a human-readable summary about an MLA using Gemini.
    
    Args:
        district: District name
        assembly_constituency: Assembly constituency name
        mla_name: Name of the MLA
        issue_category: Optional category of issue for context
        
    Returns:
        A short paragraph describing the MLA's role and responsibilities
    """
    if not client:
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
        
        response = await client.aio.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        return response.text.strip()
        
    except Exception as e:
        print(f"Gemini Summary Error: {e}")
        # Fallback to simple description
        return _get_fallback_summary(mla_name, assembly_constituency, district)

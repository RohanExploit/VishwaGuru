"""
Gemini Summary Service for Maharashtra MLA Information

Uses Gemini AI to generate human-readable summaries about MLAs and their roles.
"""
import os
import warnings
from typing import Dict, Optional

# Suppress the Future Warning from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

import google.generativeai as genai

# Simple in-memory cache to store generated summaries
# Key: (district, assembly_constituency, mla_name, issue_category)
# Value: Summary string
_summary_cache: Dict[tuple, str] = {}


# Configure Gemini (reuses existing configuration)
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


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
    # Check cache first
    cache_key = (district, assembly_constituency, mla_name, issue_category)
    if cache_key in _summary_cache:
        return _summary_cache[cache_key]

    if not api_key:
        return _get_fallback_summary(mla_name, assembly_constituency, district)
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        
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
        summary = response.text.strip()

        # Store in cache
        _summary_cache[cache_key] = summary

        return summary
        
    except Exception as e:
        print(f"Gemini Summary Error: {e}")
        # Fallback to simple description
        return _get_fallback_summary(mla_name, assembly_constituency, district)

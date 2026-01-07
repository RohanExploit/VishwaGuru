"""
Gemini MLA Summary Service

Generates AI-powered summaries about MLAs using Google's Generative AI.
Caches results to improve performance.
"""
import os
import google.generativeai as genai
from typing import Dict, Optional
import warnings
from async_lru import alru_cache

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyB8_i3tbDE3GmX4CsQ8G3mD3pB2WrHi5C8")
if api_key:
    genai.configure(api_key=api_key)


def _get_fallback_summary(mla_name: str, assembly_constituency: str, district: str) -> str:
    """Generate fallback summary when Gemini is unavailable."""
    return (
        f"{mla_name} represents {assembly_constituency} in {district}, Maharashtra. "
        f"MLAs handle local infrastructure, public services, and constituent welfare."
    )


@alru_cache(maxsize=100)
async def generate_mla_summary(
    district: str,
    assembly_constituency: str,
    mla_name: str,
    issue_category: Optional[str] = None
) -> str:
    """Generate MLA role summary using Gemini. Results cached (100 entries)."""
    if not api_key:
        return _get_fallback_summary(mla_name, assembly_constituency, district)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        context = f" for {issue_category} issues" if issue_category else ""
        
        prompt = f"""
        In one short paragraph (max 100 words), explain that MLA {mla_name} 
        represents {assembly_constituency} in {district}, Maharashtra{context}, 
        and what local issues they typically handle. Keep it factual and encouraging.
        """
        
        response = await model.generate_content_async(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Gemini Error: {e}")
        return _get_fallback_summary(mla_name, assembly_constituency, district)

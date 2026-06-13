"""
Hugging Face Text Generation Service via Featherless AI Router.

Provides LLM-based text generation as a fallback/alternative to Google Gemini.
Uses the Hugging Face Inference Router with Featherless AI provider for
OpenAI-compatible completions.
"""

import os
import httpx
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
API_URL = os.getenv(
    "HF_TEXT_API_URL",
    "https://router.huggingface.co/featherless-ai/v1/completions"
)
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Default model served by featherless-ai
DEFAULT_MODEL = os.getenv("HF_TEXT_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")


# ── Core Generation Function ─────────────────────────────────────────────────
async def generate(
    prompt: str,
    max_new_tokens: int = 400,
    temperature: float = 0.7,
    top_p: float = 0.9,
    model: Optional[str] = None,
) -> str:
    """
    Generate text using Hugging Face Featherless AI completions endpoint.

    Args:
        prompt: The input prompt to send to the model.
        max_new_tokens: Maximum number of tokens to generate (default 400).
        temperature: Sampling temperature (0.0–2.0). Lower = more deterministic.
        top_p: Nucleus sampling threshold.
        model: Override the default model name.

    Returns:
        Generated text string. Falls back to a dev-mode stub if API is unavailable.
    """
    if not API_URL or not HF_TOKEN:
        logger.warning("HF_TEXT_API_URL or HF_TOKEN not configured — returning dev stub.")
        return f"[DEV MODE OUTPUT]\n{prompt[:800]}"

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "model": model or DEFAULT_MODEL,
        "prompt": prompt,
        "max_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=60.0,
            )

        if response.status_code != 200:
            logger.error(
                f"HF Text API error {response.status_code}: {response.text}"
            )
            return f"[DEV MODE OUTPUT]\n{prompt[:800]}"

        data = response.json()

        # OpenAI-compatible response format:
        # { "choices": [{ "text": "...", "index": 0, ... }] }
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("text", "").strip()

        # Fallback: some endpoints return a flat "generated_text"
        if "generated_text" in data:
            return data["generated_text"].strip()

        logger.warning(f"Unexpected HF response shape: {list(data.keys())}")
        return ""

    except httpx.TimeoutException:
        logger.error("HF Text API request timed out.")
        return f"[DEV MODE OUTPUT]\n{prompt[:800]}"
    except Exception as e:
        logger.error(f"HF Text API exception: {e}")
        return f"[DEV MODE OUTPUT]\n{prompt[:800]}"


# ── Convenience Wrappers ─────────────────────────────────────────────────────

async def generate_civic_response(
    issue_description: str,
    category: str,
    language: str = "en",
) -> Dict[str, str]:
    """
    Generate civic action content (WhatsApp, Email, X post) using HF LLM.
    Drop-in replacement for the Gemini-based action plan generator.
    """
    prompt = f"""You are a civic action assistant for Indian citizens.
A user has reported a civic issue.

Category: {category}
Description: {issue_description}

Generate the following messages in {language} language:
1. A concise WhatsApp message (max 200 chars) to send to authorities.
2. A formal email subject line.
3. A formal email body (max 150 words) addressed to the relevant authority.
4. A concise X.com (Twitter) post (max 240 chars) with relevant hashtags.

Return ONLY valid JSON with keys: "whatsapp", "email_subject", "email_body", "x_post".
Do not use markdown code fences. Just the raw JSON object."""

    raw = await generate(prompt, max_new_tokens=600, temperature=0.5)

    # Try to parse structured JSON from the response
    try:
        # Strip any accidental markdown fences
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0]
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0]
        cleaned = cleaned.strip()

        result = json.loads(cleaned)
        # Ensure all expected keys exist
        for key in ("whatsapp", "email_subject", "email_body", "x_post"):
            if key not in result:
                result[key] = ""
        return result
    except (json.JSONDecodeError, IndexError):
        logger.warning("HF LLM returned non-JSON; building fallback response.")
        return {
            "whatsapp": f"Reporting {category} issue: {issue_description[:150]}",
            "email_subject": f"Complaint regarding {category}",
            "email_body": (
                f"Respected Authority,\n\n"
                f"I am writing to report a {category} issue: {issue_description}.\n\n"
                f"Please take necessary action.\n\nSincerely,\nCitizen"
            ),
            "x_post": f"Reporting {category}: {issue_description[:180]} #CivicIssue #VishwaGuru",
        }


async def chat_with_hf_assistant(query: str) -> str:
    """
    Chat with the civic assistant using HF LLM.
    Drop-in replacement for the Gemini-based chat.
    """
    prompt = f"""You are VishwaGuru, a helpful civic assistant for Indian citizens.

User Query: {query}

Answer the user's question about civic issues, government services, or local administration.
If they ask about specific MLAs, tell them to use the "Find My MLA" feature.
Keep answers concise and helpful."""

    return await generate(prompt, max_new_tokens=400, temperature=0.6)


async def generate_mla_summary_hf(
    district: str,
    assembly_constituency: str,
    mla_name: str,
    issue_category: Optional[str] = None,
) -> str:
    """
    Generate an MLA summary using HF LLM.
    Drop-in replacement for the Gemini-based MLA summary.
    """
    category_clause = f"\nFocus on their work related to: {issue_category}" if issue_category else ""

    prompt = f"""Provide a brief summary about {mla_name}, the MLA from {assembly_constituency} constituency in {district} district, Maharashtra, India.{category_clause}

Include:
- Their party affiliation
- Key development works
- Contact information if known
- How citizens can reach them

Keep it factual, concise, and helpful for citizens."""

    return await generate(prompt, max_new_tokens=500, temperature=0.4)


# ── Health Check ──────────────────────────────────────────────────────────────

async def check_hf_text_health() -> Dict[str, Any]:
    """Check whether the HF text generation endpoint is reachable."""
    if not API_URL or not HF_TOKEN:
        return {"status": "unconfigured", "model": DEFAULT_MODEL}

    try:
        result = await generate("Say hello in one word.", max_new_tokens=10)
        ok = bool(result) and "[DEV MODE" not in result
        return {"status": "ok" if ok else "error", "model": DEFAULT_MODEL}
    except Exception as e:
        return {"status": "error", "detail": str(e), "model": DEFAULT_MODEL}

"""
Router for Hugging Face text generation API endpoints.

Provides direct access to HF LLM text generation for civic use cases.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from backend.hf_text_service import (
    generate,
    generate_civic_response,
    chat_with_hf_assistant,
    check_hf_text_health,
)

router = APIRouter()


# ── Request / Response Models ────────────────────────────────────────────────

class HFGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    max_new_tokens: int = Field(400, ge=10, le=2000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    model: Optional[str] = None


class HFGenerateResponse(BaseModel):
    text: str
    model: Optional[str] = None


class HFCivicRequest(BaseModel):
    issue_description: str = Field(..., min_length=5, max_length=2000)
    category: str = Field(..., min_length=1, max_length=100)
    language: str = Field("en", max_length=5)


class HFChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/hf/generate", response_model=HFGenerateResponse, tags=["Hugging Face"])
async def hf_generate(req: HFGenerateRequest):
    """
    Raw text generation using the Hugging Face Featherless AI completions endpoint.
    """
    try:
        text = await generate(
            prompt=req.prompt,
            max_new_tokens=req.max_new_tokens,
            temperature=req.temperature,
            model=req.model,
        )
        return HFGenerateResponse(text=text, model=req.model)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"HF text generation failed: {e}")


@router.post("/hf/civic-response", tags=["Hugging Face"])
async def hf_civic_response(req: HFCivicRequest):
    """
    Generate civic action content (WhatsApp, Email, X post) using HF LLM.
    """
    try:
        result = await generate_civic_response(
            req.issue_description, req.category, req.language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"HF civic response failed: {e}")


@router.post("/hf/chat", tags=["Hugging Face"])
async def hf_chat(req: HFChatRequest):
    """
    Chat with the civic assistant using HF LLM.
    """
    try:
        answer = await chat_with_hf_assistant(req.query)
        return {"response": answer}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"HF chat failed: {e}")


@router.get("/hf/health", tags=["Hugging Face"])
async def hf_health():
    """
    Check HF text generation API health.
    """
    return await check_hf_text_health()

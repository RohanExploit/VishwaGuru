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
    analyze_sentiment_hf,
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

class HFSentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


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

@router.post("/hf/sentiment", tags=["Hugging Face"])
async def hf_sentiment(req: HFSentimentRequest):
    """
    Analyze sentiment of given text using HF model.
    """
    try:
        result = await analyze_sentiment_hf(req.text)
        if "error" in result and not result.get("dev_mode"):
            raise HTTPException(status_code=502, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"HF sentiment analysis failed: {e}")


@router.get("/hf/health", tags=["Hugging Face"])
async def hf_health():
    """
    Check HF text generation API health.
    """
    return await check_hf_text_health()

from fastapi import UploadFile, File
import httpx
import os

@router.post("/hf/zero-shot-image", tags=["Hugging Face"])
async def hf_zero_shot_image(image: UploadFile = File(...)):
    """
    Zero-shot image classification using Hugging Face Inference API.
    """
    hf_token = os.getenv("HF_TOKEN", "")
    if not hf_token:
        raise HTTPException(status_code=500, detail="HF_TOKEN not configured")

    API_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"
    headers = {"Authorization": f"Bearer {hf_token}"}

    try:
        image_bytes = await image.read()
        payload = {
            "parameters": {"candidate_labels": ["pothole", "garbage", "vandalism", "flooding", "broken infrastructure", "stray animal", "illegal parking", "fire", "clean street", "normal road"]}
        }

        # We need to send both image and parameters. The simplest way for this API is usually
        # just sending the image and letting it classify if it's an image classification model,
        # but zero-shot requires parameters. We'll use a standard image classification model
        # or just clip. Actually, sending binary data and parameters in HF API can be tricky.
        # Let's use google/vit-base-patch16-224 which is standard image classification.

        CLASSIFY_API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                CLASSIFY_API_URL,
                headers=headers,
                data=image_bytes,
                timeout=30.0
            )

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"HF Vision API error: {response.text}")

        return {"predictions": response.json()}

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"HF Vision API request failed: {e}")

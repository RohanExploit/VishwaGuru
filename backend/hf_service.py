"""
DEPRECATED: This module is no longer used.
Please use local_ml_service.py for local ML model-based detection instead of Hugging Face API.

This file is kept for reference purposes only.
"""
import os
import io
import httpx
import base64
from typing import Union, List, Dict, Any
from PIL import Image
import asyncio
from retry_utils import exponential_backoff_retry
import logging
import base64

# Configure logging
logger = logging.getLogger(__name__)

# HF_TOKEN is optional for public models but recommended for higher limits
token = os.environ.get("HF_TOKEN")
headers = {"Authorization": f"Bearer {token}"} if token else {}
API_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"
CAPTION_API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"

async def query_hf_api(image_bytes, labels, client: httpx.AsyncClient = None):
    should_close = False
    if client is None:
        client = httpx.AsyncClient()
        should_close = True

    try:
        # The zero-shot-image-classification pipeline expects "image" and "parameters"
        # However, the Inference API for CLIP often takes raw bytes and parameters in headers or query params
        # or a specific payload structure.
        # Actually, for zero-shot image classification via API, the payload is usually:
        # { "inputs": "image_base64...", "parameters": { "candidate_labels": [...] } }
        # OR we can send raw bytes if the model supports it, but usually zero-shot needs candidate labels.

    async with httpx.AsyncClient() as new_client:
        return await _make_request(new_client, image_bytes, labels)

@exponential_backoff_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
async def _make_request_with_retry(client, image_bytes, labels):
    """
    Internal function that makes HF API request with retry logic.
    Raises exception on failure to allow retry decorator to work.
    """
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    payload = {
        "inputs": image_base64,
        "parameters": {
            "candidate_labels": labels
        }
    }

    response = await client.post(API_URL, headers=headers, json=payload, timeout=20.0)
    if response.status_code != 200:
        error_msg = f"HF API Error: {response.status_code} - {response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)
    return response.json()


async def _make_request(client, image_bytes, labels):
    """
    Makes request to Hugging Face API with retry logic and proper error handling.
    """
    try:
        response = await client.post(API_URL, headers=headers, json=payload, timeout=20.0)
        if response.status_code != 200:
            print(f"HF API Error: {response.status_code} - {response.text}")
            return []
    finally:
        if should_close:
            await client.aclose()

        payload = {
            "inputs": image_base64,
            "parameters": {
                "candidate_labels": labels
            }
        }

        try:
            response = await client.post(API_URL, headers=headers, json=payload, timeout=20.0)
            if response.status_code != 200:
                logger.error(f"HF API Error: {response.status_code} - {response.text}")
                raise ExternalAPIException("Hugging Face API", f"HTTP {response.status_code}: {response.text}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HF API HTTP Error: {e}")
            raise ExternalAPIException("Hugging Face API", str(e)) from e
        except Exception as e:
            logger.error(f"HF API Request Exception: {e}")
            raise ExternalAPIException("Hugging Face API", str(e)) from e

def _prepare_image_bytes(image: Union[Image.Image, bytes]) -> bytes:
    """
    Detects vandalism/graffiti using Zero-Shot Image Classification with CLIP (Async).
    Includes retry logic with exponential backoff for transient failures.
    """
    try:
        labels = ["graffiti", "vandalism", "spray paint", "street art", "clean wall", "public property", "normal street"]

        img_bytes = _prepare_image_bytes(image)

        results = await query_hf_api(img_bytes, labels, client)

        # Results format: [{'label': 'graffiti', 'score': 0.9}, ...]
        if not isinstance(results, list):
             return []

        vandalism_labels = ["graffiti", "vandalism", "spray paint"]
        detected = []

        for res in results:
            if isinstance(res, dict) and res.get('label') in vandalism_labels and res.get('score', 0) > 0.4:
                 detected.append({
                     "label": res['label'],
                     "confidence": res['score'],
                     "box": []
                 })
        return detected
    except Exception as e:
        logger.error(f"HF Vandalism Detection Error: {e}", exc_info=True)
        return []

async def detect_infrastructure_clip(image: Image.Image, client: httpx.AsyncClient = None):
    """
    Detects infrastructure damage using Zero-Shot Image Classification with CLIP (Async).
    Includes retry logic with exponential backoff for transient failures.
    """
    try:
        labels = ["broken streetlight", "damaged traffic sign", "fallen tree", "damaged fence", "pothole", "clean street", "normal infrastructure"]

        img_bytes = _prepare_image_bytes(image)

        results = await query_hf_api(img_bytes, labels, client)

        if not isinstance(results, list):
             return []

        damage_labels = ["broken streetlight", "damaged traffic sign", "fallen tree", "damaged fence"]
        detected = []

        for res in results:
            if isinstance(res, dict) and res.get('label') in damage_labels and res.get('score', 0) > 0.4:
                 detected.append({
                     "label": res['label'],
                     "confidence": res['score'],
                     "box": []
                 })
        return detected
    except Exception as e:
        logger.error(f"HF Infrastructure Detection Error: {e}", exc_info=True)
        return []

async def detect_flooding_clip(image: Image.Image, client: httpx.AsyncClient = None):
    """
    Detects flooding/waterlogging using Zero-Shot Image Classification with CLIP (Async).
    Includes retry logic with exponential backoff for transient failures.
    """
    try:
        labels = ["flooded street", "waterlogging", "blocked drain", "heavy rain", "dry street", "normal road"]

        img_bytes = _prepare_image_bytes(image)

        results = await query_hf_api(img_bytes, labels, client)

        if not isinstance(results, list):
             return []

        flooding_labels = ["flooded street", "waterlogging", "blocked drain", "heavy rain"]
        detected = []

        for res in results:
            if isinstance(res, dict) and res.get('label') in flooding_labels and res.get('score', 0) > 0.4:
                 detected.append({
                     "label": res['label'],
                     "confidence": res['score'],
                     "box": []
                 })
        return detected
    except Exception as e:
        logger.error(f"HF Flooding Detection Error: {e}", exc_info=True)
        return []

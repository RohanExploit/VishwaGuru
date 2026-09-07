"""
DEPRECATED: This module is no longer used.
Please use local_ml_service.py for local ML model-based detection instead of Hugging Face API.

This file is kept for reference purposes only.
"""

import base64
import io
import logging
import os

import httpx
from PIL import Image

from backend.retry_utils import exponential_backoff_retry

# Configure logging
logger = logging.getLogger(__name__)

# HF_TOKEN is optional for public models but recommended for higher limits
token = os.environ.get("HF_TOKEN")
headers = {"Authorization": f"Bearer {token}"} if token else {}
API_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"
CAPTION_API_URL = (
    "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
)


async def query_hf_api(image_bytes, labels, client=None):
    """
    Queries Hugging Face API using a shared or new HTTP client.
    """
    if client:
        return await _make_request(client, image_bytes, labels)

    async with httpx.AsyncClient() as new_client:
        return await _make_request(new_client, image_bytes, labels)


@exponential_backoff_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
async def _make_request_with_retry(client, image_bytes, labels):
    """
    Internal function that makes HF API request with retry logic.
    Raises exception on failure to allow retry decorator to work.
    """
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {"inputs": image_base64, "parameters": {"candidate_labels": labels}}

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
        return await _make_request_with_retry(client, image_bytes, labels)
    except Exception as e:
        logger.error(f"HF API Request failed after all retries: {e}", exc_info=True)
        return []


def _prepare_image_bytes(image: Image.Image | bytes) -> bytes:
    if isinstance(image, bytes):
        return image
    elif isinstance(image, Image.Image):
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="JPEG")
        return img_byte_arr.getvalue()
    else:
        raise ValueError("Unsupported image type")


async def detect_vandalism_clip(image: Image.Image | bytes, client: httpx.AsyncClient = None):
    """
    Detects vandalism/graffiti using Zero-Shot Image Classification with CLIP (Async).
    Includes retry logic with exponential backoff for transient failures.
    """
    try:
        labels = [
            "graffiti",
            "vandalism",
            "spray paint",
            "street art",
            "clean wall",
            "public property",
            "normal street",
        ]

        img_bytes = _prepare_image_bytes(image)

        results = await query_hf_api(img_bytes, labels, client=client)

        # Results format: [{'label': 'graffiti', 'score': 0.9}, ...]
        if not isinstance(results, list):
            return []

        vandalism_labels = ["graffiti", "vandalism", "spray paint"]
        detected = []

        for res in results:
            if (
                isinstance(res, dict)
                and res.get("label") in vandalism_labels
                and res.get("score", 0) > 0.4
            ):
                detected.append({"label": res["label"], "confidence": res["score"], "box": []})
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
        labels = [
            "broken streetlight",
            "damaged traffic sign",
            "fallen tree",
            "damaged fence",
            "pothole",
            "clean street",
            "normal infrastructure",
        ]

        img_bytes = _prepare_image_bytes(image)

        results = await query_hf_api(img_bytes, labels, client=client)

        if not isinstance(results, list):
            return []

        damage_labels = [
            "broken streetlight",
            "damaged traffic sign",
            "fallen tree",
            "damaged fence",
        ]
        detected = []

        for res in results:
            if (
                isinstance(res, dict)
                and res.get("label") in damage_labels
                and res.get("score", 0) > 0.4
            ):
                detected.append({"label": res["label"], "confidence": res["score"], "box": []})
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
        labels = [
            "flooded street",
            "waterlogging",
            "blocked drain",
            "heavy rain",
            "dry street",
            "normal road",
        ]

        img_bytes = _prepare_image_bytes(image)

        results = await query_hf_api(img_bytes, labels, client=client)

        if not isinstance(results, list):
            return []

        flooding_labels = ["flooded street", "waterlogging", "blocked drain", "heavy rain"]
        detected = []

        for res in results:
            if (
                isinstance(res, dict)
                and res.get("label") in flooding_labels
                and res.get("score", 0) > 0.4
            ):
                detected.append({"label": res["label"], "confidence": res["score"], "box": []})
        return detected
    except Exception as e:
        logger.error(f"HF Flooding Detection Error: {e}", exc_info=True)
        return []

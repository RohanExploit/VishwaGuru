"""Hugging Face CLIP zero-shot image classification for civic issue detection."""
import os
import io
import httpx
from PIL import Image
import asyncio

# HF token optional but recommended for higher rate limits
hf_token = os.environ.get("HF_TOKEN")
api_headers = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}
CLIP_API_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"

async def query_hf_api(image_bytes, candidate_labels):
    """Query CLIP API with image and candidate labels."""
    async with httpx.AsyncClient() as client:
        import base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        request_payload = {
            "inputs": image_base64,
            "parameters": {
                "candidate_labels": candidate_labels
            }
        }

        try:
            response = await client.post(CLIP_API_URL, headers=api_headers, json=request_payload, timeout=20.0)
            if response.status_code != 200:
                print(f"HF API Error: {response.status_code} - {response.text}")
                return []
            return response.json()
        except Exception as e:
            print(f"HF API Request Exception: {e}")
            return []

async def detect_vandalism_clip(image: Image.Image):
    """Detect vandalism/graffiti using CLIP zero-shot classification."""
    try:
        labels = ["graffiti", "vandalism", "spray paint", "street art", "clean wall", "public property", "normal street"]

        img_buffer = io.BytesIO()
        image.save(img_buffer, format=image.format if image.format else 'JPEG')
        img_bytes = img_buffer.getvalue()

        results = await query_hf_api(img_bytes, labels)

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
        print(f"Vandalism Detection Error: {e}")
        return []

async def detect_infrastructure_clip(image: Image.Image):
    """Detect infrastructure damage (lights, signs, trees, fences) using CLIP."""
    try:
        labels = ["broken streetlight", "damaged traffic sign", "fallen tree", "damaged fence", "pothole", "clean street", "normal infrastructure"]

        img_buffer = io.BytesIO()
        image.save(img_buffer, format=image.format if image.format else 'JPEG')
        img_bytes = img_buffer.getvalue()

        results = await query_hf_api(img_bytes, labels)

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
        print(f"Infrastructure Detection Error: {e}")
        return []

async def detect_flooding_clip(image: Image.Image):
    """Detect flooding and water damage using CLIP."""
    try:
        labels = ["flooding", "water damage", "wet ground", "submerged", "dry ground", "normal"]

        img_buffer = io.BytesIO()
        image.save(img_buffer, format=image.format if image.format else 'JPEG')
        img_bytes = img_buffer.getvalue()

        results = await query_hf_api(img_bytes, labels)

        if not isinstance(results, list):
             return []

        flood_labels = ["flooding", "water damage", "wet ground", "submerged"]
        detected = []

        for res in results:
            if isinstance(res, dict) and res.get('label') in flood_labels and res.get('score', 0) > 0.4:
                 detected.append({
                     "label": res['label'],
                     "confidence": res['score'],
                     "box": []
                 })
        return detected
    except Exception as e:
        print(f"Flooding Detection Error: {e}")
        return []

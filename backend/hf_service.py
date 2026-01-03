import os
import io
import httpx
from PIL import Image
import asyncio

# HF_TOKEN is optional for public models but recommended for higher limits
token = os.environ.get("HF_TOKEN")
headers = {"Authorization": f"Bearer {token}"} if token else {}
API_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"

async def query_hf_api(image_bytes, labels):
    async with httpx.AsyncClient() as client:
        # The zero-shot-image-classification pipeline expects "image" and "parameters"
        # However, the Inference API for CLIP often takes raw bytes and parameters in headers or query params
        # or a specific payload structure.
        # Actually, for zero-shot image classification via API, the payload is usually:
        # { "inputs": "image_base64...", "parameters": { "candidate_labels": [...] } }
        # OR we can send raw bytes if the model supports it, but usually zero-shot needs candidate labels.

        # Let's check the HF Inference API docs for zero-shot-image-classification.
        # It typically expects a JSON payload with 'inputs' (image) and 'parameters' (candidate_labels).
        # We need to base64 encode the image.

        import base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        payload = {
            "inputs": image_base64,
            "parameters": {
                "candidate_labels": labels
            }
        }

        try:
            response = await client.post(API_URL, headers=headers, json=payload, timeout=20.0)
            if response.status_code != 200:
                print(f"HF API Error: {response.status_code} - {response.text}")
                return []
            return response.json()
        except Exception as e:
            print(f"HF API Request Exception: {e}")
            return []

async def detect_vandalism_clip(image: Image.Image):
    """
    Detects vandalism/graffiti using Zero-Shot Image Classification with CLIP (Async).
    """
    try:
        labels = ["graffiti", "vandalism", "spray paint", "street art", "clean wall", "public property", "normal street"]

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
        img_bytes = img_byte_arr.getvalue()

        results = await query_hf_api(img_bytes, labels)

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
        print(f"HF Detection Error: {e}")
        return []

async def detect_traffic_violation_clip(image: Image.Image):
    try:
        labels = ["illegal parking", "car blocking driveway", "double parking", "blocked road", "traffic violation", "normal street", "parked car", "moving car"]

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
        img_bytes = img_byte_arr.getvalue()

        results = await query_hf_api(img_bytes, labels)

        if not isinstance(results, list):
             return []

        violation_labels = ["illegal parking", "car blocking driveway", "double parking", "blocked road", "traffic violation"]
        detected = []

        for res in results:
            if isinstance(res, dict) and res.get('label') in violation_labels and res.get('score', 0) > 0.4:
                 detected.append({
                     "label": res['label'],
                     "confidence": res['score'],
                     "box": []
                 })
        return detected
    except Exception as e:
        print(f"HF Detection Error: {e}")
        return []

async def detect_infrastructure_clip(image: Image.Image):
    try:
        labels = ["broken streetlight", "damaged traffic sign", "fallen tree", "damaged fence", "pothole", "clean street", "normal infrastructure"]

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
        img_bytes = img_byte_arr.getvalue()

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
        print(f"HF Detection Error: {e}")
        return []

async def detect_flooding_clip(image: Image.Image):
    try:
        labels = ["flooded street", "waterlogging", "blocked drain", "heavy rain", "dry street", "normal road"]

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
        img_bytes = img_byte_arr.getvalue()

        results = await query_hf_api(img_bytes, labels)

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
        print(f"HF Detection Error: {e}")
        return []

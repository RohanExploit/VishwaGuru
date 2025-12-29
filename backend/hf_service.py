import httpx
import os
import json
from typing import List, Dict, Union
import base64

HF_API_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"

async def classify_image_zero_shot(image_bytes: bytes, candidate_labels: List[str]):
    api_key = os.environ.get("HF_TOKEN")
    if not api_key:
         return {"error": "HF_TOKEN not configured"}

    headers = {"Authorization": f"Bearer {api_key}"}

    # Convert image to base64
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "inputs": base64_image,
        "parameters": {
            "candidate_labels": candidate_labels
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(HF_API_URL, headers=headers, json=payload, timeout=20.0)
            if response.status_code != 200:
                 # Fallback: maybe the model doesn't support this pipeline via API directly or needs different format
                 print(f"HF API Error: {response.status_code} - {response.text}")
                 return {"error": f"HF API Error: {response.text}"}

            result = response.json()
            # Result usually: [{"score": 0.99, "label": "graffiti"}, ...]
            return result
        except Exception as e:
            return {"error": str(e)}

import os
import io
import httpx
import base64
from typing import Union, List, Dict, Any
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# HF_TOKEN should be set in environment variables
token = os.environ.get("HF_TOKEN")
headers = {"Authorization": f"Bearer {token}"} if token else {}

# Zero-Shot Image Classification Model
CLIP_API_URL = "https://router.huggingface.co/models/openai/clip-vit-base-patch32"

# Image Captioning Model
CAPTION_API_URL = "https://router.huggingface.co/models/Salesforce/blip-image-captioning-large"

# Sentiment Analysis / Text Classification Model
SENTIMENT_API_URL = "https://router.huggingface.co/models/cardiffnlp/twitter-roberta-base-sentiment-latest"

# Visual Question Answering Model
VQA_API_URL = "https://router.huggingface.co/models/dandelin/vilt-b32-finetuned-vqa"

# Depth Estimation Model
DEPTH_API_URL = "https://router.huggingface.co/models/Intel/dpt-hybrid-midas"

# Audio Classification Model
AUDIO_CLASS_API_URL = "https://router.huggingface.co/models/MIT/ast-finetuned-audioset-10-10-0.4593"

# Speech-to-Text Model (Whisper)
WHISPER_API_URL = "https://router.huggingface.co/models/openai/whisper-large-v3-turbo"

async def _make_request(client, url, payload):
    try:
        response = await client.post(url, headers=headers, json=payload, timeout=20.0)
        if response.status_code != 200:
            logger.error(f"HF API Error ({url}): {response.status_code} - {response.text}")
            return []
        return response.json()
    except Exception as e:
        logger.error(f"HF API Request Exception: {e}")
        return []

def _prepare_image_bytes(image: Union[Image.Image, bytes]) -> bytes:
    if isinstance(image, bytes):
        return image
    img_byte_arr = io.BytesIO()
    fmt = image.format if image.format else 'JPEG'
    image.save(img_byte_arr, format=fmt)
    return img_byte_arr.getvalue()

async def query_hf_api(image_bytes, labels, client=None):
    """
    Queries Hugging Face CLIP API for zero-shot image classification.
    """
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    payload = {
        "inputs": image_base64,
        "parameters": {"candidate_labels": labels}
    }

    if client:
        return await _make_request(client, CLIP_API_URL, payload)

    async with httpx.AsyncClient() as new_client:
        return await _make_request(new_client, CLIP_API_URL, payload)

async def _detect_clip_generic(image: Union[Image.Image, bytes], labels: List[str], target_labels: List[str], client: httpx.AsyncClient = None):
    try:
        img_bytes = _prepare_image_bytes(image)
        results = await query_hf_api(img_bytes, labels, client=client)

        if not isinstance(results, list):
             return []

        detected = []
        for res in results:
            if isinstance(res, dict) and res.get('label') in target_labels and res.get('score', 0) > 0.4:
                 detected.append({
                     "label": res['label'],
                     "confidence": res['score'],
                     "box": [] # CLIP doesn't provide boxes, but frontend expects this structure
                 })
        return detected
    except Exception as e:
        logger.error(f"HF Detection Error: {e}")
        return []

# --- Specific Detectors ---

async def detect_illegal_parking_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    labels = ["illegal parking", "car blocking driveway", "double parked", "car on sidewalk", "legal parking", "empty street"]
    targets = ["illegal parking", "car blocking driveway", "double parked", "car on sidewalk"]
    return await _detect_clip_generic(image, labels, targets, client)

async def detect_street_light_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    labels = ["broken streetlight", "dark street", "street light off", "working streetlight", "daytime"]
    targets = ["broken streetlight", "dark street", "street light off"]
    return await _detect_clip_generic(image, labels, targets, client)

async def detect_fire_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    labels = ["fire", "smoke", "flames", "burning", "normal scene", "safe"]
    targets = ["fire", "smoke", "flames", "burning"]
    return await _detect_clip_generic(image, labels, targets, client)

async def detect_stray_animal_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    labels = ["stray dog", "stray cow", "cattle on road", "animal", "empty road"]
    targets = ["stray dog", "stray cow", "cattle on road", "animal"]
    return await _detect_clip_generic(image, labels, targets, client)

async def detect_blocked_road_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    labels = ["blocked road", "road debris", "construction block", "traffic jam", "clear road"]
    targets = ["blocked road", "road debris", "construction block"]
    return await _detect_clip_generic(image, labels, targets, client)

async def detect_tree_hazard_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    labels = ["fallen tree", "broken branch", "hanging branch", "healthy tree", "no tree"]
    targets = ["fallen tree", "broken branch", "hanging branch"]
    return await _detect_clip_generic(image, labels, targets, client)

async def detect_pest_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    labels = ["rat", "cockroach", "mosquito swarm", "pest infestation", "clean", "no pests"]
    targets = ["rat", "cockroach", "mosquito swarm", "pest infestation"]
    return await _detect_clip_generic(image, labels, targets, client)

async def detect_water_leak_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    labels = ["water leak", "burst pipe", "flooded floor", "puddle", "dry floor", "no water"]
    targets = ["water leak", "burst pipe", "flooded floor", "puddle"]
    return await _detect_clip_generic(image, labels, targets, client)

async def detect_accessibility_issue_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    labels = ["blocked wheelchair ramp", "stairs without ramp", "broken ramp", "accessible path", "wheelchair accessible", "clear path"]
    targets = ["blocked wheelchair ramp", "stairs without ramp", "broken ramp"]
    return await _detect_clip_generic(image, labels, targets, client)

async def detect_crowd_density_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    labels = ["dense crowd", "dangerous overcrowding", "sparse crowd", "empty space", "safe crowd level"]
    # We want to detect high density
    targets = ["dense crowd", "dangerous overcrowding"]
    return await _detect_clip_generic(image, labels, targets, client)

async def detect_audio_event(audio_bytes: bytes, client: httpx.AsyncClient = None):
    """
    Detects audio events from audio bytes using MIT/ast-finetuned-audioset-10-10-0.4593.
    """
    # The Audio Classification API accepts raw audio bytes
    try:
        headers_bin = {"Authorization": f"Bearer {token}"} if token else {}
        async def do_post(c):
             return await c.post(AUDIO_CLASS_API_URL, headers=headers_bin, content=audio_bytes, timeout=30.0)

        if client:
            response = await do_post(client)
        else:
            async with httpx.AsyncClient() as new_client:
                response = await do_post(new_client)

        if response.status_code == 200:
            # Result is usually [{"score": 0.9, "label": "speech"}, ...]
            data = response.json()
            return data
        else:
            logger.error(f"Audio API Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Audio Detection Error: {e}")
        return []

async def detect_severity_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    """
    Returns a severity object: {level: 'High', confidence: 0.9, raw_label: 'critical...'}
    """
    labels = ["critical emergency", "high urgency", "medium urgency", "low urgency", "safe situation"]
    img_bytes = _prepare_image_bytes(image)
    results = await query_hf_api(img_bytes, labels, client=client)

    if isinstance(results, list) and len(results) > 0:
        top = results[0]
        label = top.get('label')
        score = top.get('score', 0)

        level = "Low"
        if label == "critical emergency": level = "Critical"
        elif label == "high urgency": level = "High"
        elif label == "medium urgency": level = "Medium"

        return {"level": level, "confidence": score, "raw_label": label}

    return {"level": "Unknown", "confidence": 0, "raw_label": "unknown"}

async def detect_smart_scan_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    """
    Auto-detects category from image.
    """
    labels = [
        "pothole", "garbage", "flooded street", "fire accident",
        "fallen tree", "stray animal", "blocked road", "broken streetlight",
        "illegal parking", "graffiti vandalism", "normal street"
    ]
    img_bytes = _prepare_image_bytes(image)
    results = await query_hf_api(img_bytes, labels, client=client)

    if isinstance(results, list) and len(results) > 0:
        top = results[0]
        # Map label to internal category ID if needed, or return raw
        return {
            "category": top.get('label'),
            "confidence": top.get('score'),
            "all_scores": results[:3]
        }
    return {"category": "unknown", "confidence": 0}

async def generate_image_caption(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    """
    Generates a description using BLIP model.
    """
    img_bytes = _prepare_image_bytes(image)
    image_base64 = base64.b64encode(img_bytes).decode('utf-8')
    payload = {"inputs": image_base64} # BLIP API usually takes raw bytes or base64?
    # Standard Inference API for image-to-text usually takes raw bytes body

    # NOTE: The standard Inference API for image-to-text (BLIP) accepts binary body.
    # The _make_request helper assumes JSON. Let's handle this separately.

    try:
        headers_bin = {"Authorization": f"Bearer {token}"} if token else {}
        async def do_post(c):
             return await c.post(CAPTION_API_URL, headers=headers_bin, content=img_bytes, timeout=20.0)

        if client:
            response = await do_post(client)
        else:
            async with httpx.AsyncClient() as new_client:
                response = await do_post(new_client)

        if response.status_code == 200:
            # Result is usually [{"generated_text": "..."}]
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0].get('generated_text', '')
            if isinstance(data, dict):
                return data.get('generated_text', '')
        else:
            logger.error(f"Caption API Error: {response.status_code} - {response.text}")
            return ""
    except Exception as e:
        logger.error(f"Caption Generation Error: {e}")
        return ""
    return ""

async def analyze_urgency_text(text: str, client: httpx.AsyncClient = None):
    """
    Analyzes text urgency using Sentiment Analysis.
    Negative sentiment -> Higher Urgency.
    """
    if not text: return {"urgency": "Low", "score": 0}

    payload = {"inputs": text}

    if client:
        result = await _make_request(client, SENTIMENT_API_URL, payload)
    else:
        async with httpx.AsyncClient() as new_client:
            result = await _make_request(new_client, SENTIMENT_API_URL, payload)

    # Result format: [[{'label': 'negative', 'score': 0.9}, ...]] (nested list)
    if isinstance(result, list) and len(result) > 0:
        scores = result[0] # List of dicts
        if isinstance(scores, list):
            # Find label with highest score
            top = max(scores, key=lambda x: x['score'])
            label = top['label'] # 'positive', 'neutral', 'negative'
            score = top['score']

            urgency = "Low"
            if label == "negative":
                urgency = "High"
            elif label == "neutral":
                urgency = "Medium"

            return {"urgency": urgency, "score": score, "sentiment": label}

    return {"urgency": "Low", "score": 0, "sentiment": "unknown"}


async def verify_resolution_vqa(image: Union[Image.Image, bytes], question: str, client: httpx.AsyncClient = None):
    """
    Uses VQA to verify if an issue is resolved based on a question.
    """
    img_bytes = _prepare_image_bytes(image)
    image_base64 = base64.b64encode(img_bytes).decode('utf-8')

    payload = {
        "inputs": {
            "image": image_base64,
            "question": question
        }
    }

    if client:
        result = await _make_request(client, VQA_API_URL, payload)
    else:
        async with httpx.AsyncClient() as new_client:
            result = await _make_request(new_client, VQA_API_URL, payload)

    # Result format: [{'answer': 'yes', 'score': 0.9}, ...]
    if isinstance(result, list) and len(result) > 0:
        top = result[0]
        return {
            "answer": top.get('answer'),
            "confidence": top.get('score'),
            "all_answers": result[:3]
        }

    return {"answer": "unknown", "confidence": 0}

async def detect_depth_map(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    """
    Generates a depth map for the given image using Intel/dpt-hybrid-midas.
    Returns a Base64 encoded string of the depth map image.
    """
    img_bytes = _prepare_image_bytes(image)

    # The DPT model expects raw image bytes as input and returns raw image bytes (JPEG/PNG)
    try:
        headers_bin = {"Authorization": f"Bearer {token}"} if token else {}
        async def do_post(c):
             return await c.post(DEPTH_API_URL, headers=headers_bin, content=img_bytes, timeout=30.0)

        if client:
            response = await do_post(client)
        else:
            async with httpx.AsyncClient() as new_client:
                response = await do_post(new_client)

        if response.status_code == 200:
            # Response is a binary image
            response_bytes = response.content
            # Convert to base64
            b64_img = base64.b64encode(response_bytes).decode('utf-8')
            return {"depth_map": b64_img}
        else:
            logger.error(f"Depth API Error: {response.status_code} - {response.text}")
            return {"error": "Failed to generate depth map", "details": response.text}

    except Exception as e:
        logger.error(f"Depth Estimation Error: {e}")
        return {"error": str(e)}

async def transcribe_audio(audio_bytes: bytes, client: httpx.AsyncClient = None):
    """
    Transcribes audio using OpenAI Whisper model via HF API.
    """
    try:
        headers_bin = {"Authorization": f"Bearer {token}"} if token else {}
        async def do_post(c):
             return await c.post(WHISPER_API_URL, headers=headers_bin, content=audio_bytes, timeout=60.0)

        if client:
            response = await do_post(client)
        else:
            async with httpx.AsyncClient() as new_client:
                response = await do_post(new_client)

        if response.status_code == 200:
            # Result: {"text": "..."}
            data = response.json()
            return data.get("text", "")
        else:
            logger.error(f"Whisper API Error: {response.status_code} - {response.text}")
            return ""
    except Exception as e:
        logger.error(f"Audio Transcription Error: {e}")
        return ""

async def detect_waste_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    """
    Classifies waste type for sorting.
    """
    labels = ["plastic bottle", "glass bottle", "metal can", "paper cardboard", "organic food waste", "electronic waste", "general trash"]

    img_bytes = _prepare_image_bytes(image)
    results = await query_hf_api(img_bytes, labels, client=client)

    if isinstance(results, list) and len(results) > 0:
        top = results[0]
        return {
            "waste_type": top.get('label'),
            "confidence": top.get('score'),
            "all_scores": results[:3]
        }
    return {"waste_type": "unknown", "confidence": 0}

async def detect_civic_eye_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    """
    Performs a comprehensive assessment of the scene.
    """
    # 1. Safety
    safety_labels = ["safe area", "unsafe area", "dangerous situation", "secure environment"]

    # 2. Cleanliness
    clean_labels = ["clean street", "dirty street", "garbage piled up", "spotless area"]

    # 3. Infrastructure
    infra_labels = ["good infrastructure", "broken infrastructure", "potholes", "well maintained road"]

    img_bytes = _prepare_image_bytes(image)

    # We can do 3 separate calls or 1 big call. CLIP handles many labels well.
    all_labels = safety_labels + clean_labels + infra_labels

    results = await query_hf_api(img_bytes, all_labels, client=client)

    if not isinstance(results, list):
        return {"error": "Analysis failed"}

    def get_top_category(res_list, category_labels):
        relevant = [r for r in res_list if r.get('label') in category_labels]
        if relevant:
            return relevant[0]
        return {"label": "unknown", "score": 0}

    safety = get_top_category(results, safety_labels)
    cleanliness = get_top_category(results, clean_labels)
    infra = get_top_category(results, infra_labels)

    return {
        "safety": {"status": safety['label'], "score": safety['score']},
        "cleanliness": {"status": cleanliness['label'], "score": cleanliness['score']},
        "infrastructure": {"status": infra['label'], "score": infra['score']}
    }

async def detect_graffiti_art_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    """
    Distinguish between artistic mural (legal) and graffiti vandalism (illegal).
    """
    labels = ["artistic mural", "street art", "graffiti tag", "vandalism", "clean wall"]
    targets = ["artistic mural", "street art", "graffiti tag", "vandalism"]
    return await _detect_clip_generic(image, labels, targets, client)

async def detect_traffic_sign_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    """
    Detects damaged or vandalized traffic signs.
    """
    labels = ["damaged traffic sign", "graffiti on sign", "bent sign", "faded sign", "clear traffic sign"]
    targets = ["damaged traffic sign", "graffiti on sign", "bent sign", "faded sign"]
    return await _detect_clip_generic(image, labels, targets, client)

async def detect_abandoned_vehicle_clip(image: Union[Image.Image, bytes], client: httpx.AsyncClient = None):
    """
    Detects abandoned or wrecked vehicles.
    """
    labels = ["abandoned car", "rusted vehicle", "car with flat tires", "wrecked car", "normal parked car"]
    targets = ["abandoned car", "rusted vehicle", "car with flat tires", "wrecked car"]
    return await _detect_clip_generic(image, labels, targets, client)

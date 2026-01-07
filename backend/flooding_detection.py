"""Flooding detection wrapper using HF Service."""
from PIL import Image
from hf_service import detect_flooding_clip

def detect_flooding(image: Image.Image):
    """Detect flooding/water damage. Async wrapper for CLIP model."""
    return detect_flooding_clip(image)

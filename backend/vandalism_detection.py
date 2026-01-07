"""Vandalism detection wrapper using HF Service."""
from hf_service import detect_vandalism_clip
from PIL import Image

def detect_vandalism(image: Image.Image):
    """Detect vandalism/graffiti. Async wrapper for CLIP model."""
    return detect_vandalism_clip(image)

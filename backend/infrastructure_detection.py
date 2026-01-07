"""Infrastructure damage detection wrapper using HF Service."""
from hf_service import detect_infrastructure_clip
from PIL import Image

def detect_infrastructure(image: Image.Image):
    """Detect infrastructure damage (lights, signs, fences). Async wrapper for CLIP."""
    return detect_infrastructure_clip(image)

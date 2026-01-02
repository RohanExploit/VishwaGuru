from hf_service import detect_fire_clip
from PIL import Image

def detect_fire(image: Image.Image):
    """
    Wrapper for fire detection using HF Service.
    """
    return detect_fire_clip(image)

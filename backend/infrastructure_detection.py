from hf_service import detect_infrastructure_clip
from PIL import Image

def detect_infrastructure(image: Image.Image):
    """
    Wrapper for infrastructure damage detection using HF Service.
    """
    return detect_infrastructure_clip(image)

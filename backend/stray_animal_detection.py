from hf_service import detect_stray_animal_clip
from PIL import Image

def detect_stray_animal(image: Image.Image):
    """
    Wrapper for stray animal detection using HF Service.
    """
    return detect_stray_animal_clip(image)

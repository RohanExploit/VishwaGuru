import io
import httpx
from PIL import Image
from backend.hf_service import detect_flooding_clip

async def detect_flooding(image: Image.Image):
    """
    Detects flooding/waterlogging using Zero-Shot Image Classification with CLIP.
    """
    return await detect_flooding_clip(image)

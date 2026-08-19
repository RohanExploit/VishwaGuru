from PIL import Image

from backend.local_ml_service import detect_vandalism_local


async def detect_vandalism(image: Image.Image):
    """
    Wrapper for vandalism detection using Local ML Service.
    """
    return await detect_vandalism_local(image)

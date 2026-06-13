from backend.local_ml_service import detect_infrastructure_local
from PIL import Image

async def detect_infrastructure(image: Image.Image):
    """
    Wrapper for infrastructure damage detection using Local ML Service.
    """
    return await detect_infrastructure_local(image)

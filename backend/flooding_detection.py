from PIL import Image
from local_ml_service import detect_flooding_local

async def detect_flooding(image: Image.Image):
    """
    Detects flooding in an image.
    Delegates to the Local ML Service.
    """
    return await detect_flooding_local(image)

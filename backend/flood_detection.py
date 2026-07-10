from PIL import Image
import io
import httpx
from hf_service import query_hf_api
import asyncio

_hf_client = httpx.AsyncClient()

def detect_flooding(image: Image.Image):
    """
    Detects flooding/waterlogging using Zero-Shot Image Classification with CLIP.
    """
    try:
        # labels to classify
        labels = ["flooded street", "waterlogging", "heavy rain", "submerged car", "dry road", "normal street"]

        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If we're already in an async context, this synchronous function won't work easily with our async HF client wrapper.
            # But we can try to fall back or spawn a thread if really needed. For now, try running synchronously using asyncio.run if possible.
            import threading
            def _run():
                return asyncio.run(query_hf_api(img_byte_arr, labels, _hf_client))
            # Just do a blocking call inside a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                results = pool.submit(_run).result()
        else:
            results = asyncio.run(query_hf_api(img_byte_arr, labels, _hf_client))

        # Filter for flooding related
        flood_labels = ["flooded street", "waterlogging", "submerged car"]
        detected = []

        for res in results:
            if res['label'] in flood_labels and res['score'] > 0.4: # Threshold
                 detected.append({
                     "label": res['label'],
                     "confidence": res['score'],
                     "box": [] # Classification only
                 })

        return detected

    except Exception as e:
        print(f"Flooding Detection Error: {e}")
        return []

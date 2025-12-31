from hf_service import client
from PIL import Image
import io

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

        # Using the same model as vandalism for consistency and caching benefits
        results = client.zero_shot_image_classification(
            image=img_byte_arr,
            labels=labels,
            model="openai/clip-vit-base-patch32"
        )

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

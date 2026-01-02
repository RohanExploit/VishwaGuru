import os
from huggingface_hub import InferenceClient
from PIL import Image
import io

# Initialize client
# HF_TOKEN is optional for public models but recommended for higher limits
# If token is None, it runs without authentication (public access)
token = os.environ.get("HF_TOKEN")
client = InferenceClient(token=token)

def detect_vandalism_clip(image: Image.Image):
    """
    Detects vandalism/graffiti using Zero-Shot Image Classification with CLIP.
    """
    try:
        # labels to classify
        labels = ["graffiti", "vandalism", "spray paint", "street art", "clean wall", "public property", "normal street"]

        # InferenceClient.zero_shot_image_classification
        # We need to send image bytes
        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        results = client.zero_shot_image_classification(
            image=img_byte_arr,
            labels=labels,
            model="openai/clip-vit-base-patch32"
        )

        # Results is a list of dicts: [{'label': 'graffiti', 'score': 0.9}, ...]
        # Filter for vandalism related
        vandalism_labels = ["graffiti", "vandalism", "spray paint"]
        detected = []

        for res in results:
            if res['label'] in vandalism_labels and res['score'] > 0.4: # Threshold
                 detected.append({
                     "label": res['label'],
                     "confidence": res['score'],
                     "box": [] # CLIP doesn't give boxes, it's classification
                 })

        return detected

    except Exception as e:
        print(f"HF Detection Error: {e}")
        # Return empty list on error
        return []

def detect_fire_clip(image: Image.Image):
    """
    Detects fire/smoke using Zero-Shot Image Classification with CLIP.
    """
    try:
        # labels to classify
        labels = ["fire", "smoke", "burning", "forest fire", "building fire", "normal scene", "clear sky"]

        # InferenceClient.zero_shot_image_classification
        # We need to send image bytes
        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        results = client.zero_shot_image_classification(
            image=img_byte_arr,
            labels=labels,
            model="openai/clip-vit-base-patch32"
        )

        # Results is a list of dicts: [{'label': 'fire', 'score': 0.9}, ...]
        # Filter for fire related
        fire_labels = ["fire", "smoke", "burning", "forest fire", "building fire"]
        detected = []

        for res in results:
            if res['label'] in fire_labels and res['score'] > 0.4: # Threshold
                 detected.append({
                     "label": res['label'],
                     "confidence": res['score'],
                     "box": [] # CLIP doesn't give boxes, it's classification
                 })

        return detected

    except Exception as e:
        print(f"HF Detection Error: {e}")
        # Return empty list on error
        return []

def detect_stray_animal_clip(image: Image.Image):
    """
    Detects stray animals (dogs, cows, etc.) using Zero-Shot Image Classification with CLIP.
    """
    try:
        # labels to classify
        labels = ["stray dog", "stray cow", "cattle on road", "wild animal", "normal street", "empty road", "pedestrian"]

        # InferenceClient.zero_shot_image_classification
        # We need to send image bytes
        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        results = client.zero_shot_image_classification(
            image=img_byte_arr,
            labels=labels,
            model="openai/clip-vit-base-patch32"
        )

        # Results is a list of dicts: [{'label': 'stray dog', 'score': 0.9}, ...]
        # Filter for animal related
        animal_labels = ["stray dog", "stray cow", "cattle on road", "wild animal"]
        detected = []

        for res in results:
            if res['label'] in animal_labels and res['score'] > 0.4: # Threshold
                 detected.append({
                     "label": res['label'],
                     "confidence": res['score'],
                     "box": [] # CLIP doesn't give boxes, it's classification
                 })

        return detected

    except Exception as e:
        print(f"HF Detection Error: {e}")
        # Return empty list on error
        return []

def detect_infrastructure_clip(image: Image.Image):
    """
    Detects broken infrastructure (streetlights, signs) using Zero-Shot Image Classification with CLIP.
    """
    try:
        # labels to classify
        labels = ["broken streetlight", "damaged traffic sign", "fallen tree", "damaged fence", "pothole", "clean street", "normal infrastructure"]

        # InferenceClient.zero_shot_image_classification
        # We need to send image bytes
        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        results = client.zero_shot_image_classification(
            image=img_byte_arr,
            labels=labels,
            model="openai/clip-vit-base-patch32"
        )

        # Results is a list of dicts: [{'label': 'broken streetlight', 'score': 0.9}, ...]
        # Filter for infrastructure damage related
        damage_labels = ["broken streetlight", "damaged traffic sign", "fallen tree", "damaged fence"]
        detected = []

        for res in results:
            if res['label'] in damage_labels and res['score'] > 0.4: # Threshold
                 detected.append({
                     "label": res['label'],
                     "confidence": res['score'],
                     "box": [] # CLIP doesn't give boxes, it's classification
                 })

        return detected

    except Exception as e:
        print(f"HF Detection Error: {e}")
        # Return empty list on error
        return []

def detect_flooding_clip(image: Image.Image):
    """
    Detects flooding/waterlogging using Zero-Shot Image Classification with CLIP.
    """
    try:
        # labels to classify
        labels = ["flooded street", "waterlogging", "blocked drain", "heavy rain", "dry street", "normal road"]

        # InferenceClient.zero_shot_image_classification
        # We need to send image bytes
        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        results = client.zero_shot_image_classification(
            image=img_byte_arr,
            labels=labels,
            model="openai/clip-vit-base-patch32"
        )

        # Results is a list of dicts: [{'label': 'flooded street', 'score': 0.9}, ...]
        # Filter for flooding related
        flooding_labels = ["flooded street", "waterlogging", "blocked drain", "heavy rain"]
        detected = []

        for res in results:
            if res['label'] in flooding_labels and res['score'] > 0.4: # Threshold
                 detected.append({
                     "label": res['label'],
                     "confidence": res['score'],
                     "box": [] # CLIP doesn't give boxes, it's classification
                 })

        return detected

    except Exception as e:
        print(f"HF Detection Error: {e}")
        # Return empty list on error
        return []

import os
import io
from huggingface_hub import AsyncInferenceClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HF_TOKEN = os.environ.get("HF_TOKEN")

async def analyze_civic_issue(image_bytes: bytes) -> dict:
    """
    Analyzes an image using Hugging Face's Zero-Shot Classification model (CLIP).
    Identifies civic issues like potholes, garbage, etc. without training a custom model.
    """
    try:
        # Initialize client
        # If HF_TOKEN is missing, it might use the public API (rate limited)
        client = AsyncInferenceClient(token=HF_TOKEN)

        # Model: openai/clip-vit-base-patch32
        # This model connects text and images, allowing us to ask "is this a pothole?"
        model = "openai/clip-vit-base-patch32"

        # Candidate labels for the model to choose from
        labels = [
            "large pothole in road",
            "overflowing garbage pile",
            "broken street light",
            "heavy traffic jam",
            "flooded water logged street",
            "graffiti vandalism",
            "broken sidewalk",
            "clean road",
            "fire accident"
        ]

        logger.info(f"Analyzing image with HF model: {model}")

        # Perform Zero-Shot Image Classification
        result = await client.zero_shot_image_classification(
            image=image_bytes,
            model=model,
            labels=labels
        )

        # Result format is a list of dicts sorted by score: [{'label': '...', 'score': 0.9}, ...]
        if not result:
            return {"label": "Unknown", "confidence": 0.0}

        top_result = result[0]
        logger.info(f"Analysis result: {top_result}")

        return {
            "label": top_result["label"],
            "confidence": top_result["score"],
            "all_predictions": result[:3]  # Return top 3 for UI context
        }

    except Exception as e:
        logger.error(f"Hugging Face Analysis Error: {e}")
        # Graceful degradation
        return {
            "error": str(e),
            "label": "Analysis Service Unavailable",
            "confidence": 0.0
        }

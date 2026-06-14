import logging
import threading
from typing import Optional, Any

from backend.exceptions import ModelLoadException, DetectionException

# Configure logging
logger = logging.getLogger(__name__)

# Thread-safe singleton pattern for model loading
# This prevents race conditions when multiple threads try to load the model simultaneously
_model: Optional[Any] = None
_model_lock: threading.Lock = threading.Lock()
_model_loading_error: Optional[Exception] = None
_model_initialized: bool = False

def is_model_available():
    """
    Checks if the model dependencies are available.
    """
    try:
        import ultralyticsplus
        return True
    except ImportError:
        return False

def load_model():
    """
    Loads the YOLO model lazily.
    The model file will be downloaded on the first call if not cached.
    This prevents blocking the application startup.
    
    Returns:
        The loaded YOLO model instance.
        
    Raises:
        Exception: If model loading fails.
    """
    logger.info("Loading Pothole Detection Model...")
    try:
        # Move import here to prevent blocking startup with heavy imports/checks
        from ultralyticsplus import YOLO

        model = YOLO('keremberke/yolov8n-pothole-segmentation')

        # set model parameters
        model.overrides['conf'] = 0.25  # NMS confidence threshold
        model.overrides['iou'] = 0.45  # NMS IoU threshold
        model.overrides['agnostic_nms'] = False  # NMS class-agnostic
        model.overrides['max_det'] = 1000  # maximum number of detections per image

        logger.info("Model loaded successfully.")
        return model
    except ImportError:
        logger.warning("ultralyticsplus not installed. Pothole detection disabled.")
        return None
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None


def get_model():
    global _model
    # Double-checked locking pattern to ensure thread safety
    # This prevents multiple threads from loading the heavy model simultaneously
    # while avoiding locking overhead for subsequent calls.
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = load_model()
    return _model

def detect_potholes(image_source):
    """
    Detects potholes in an image.

    Args:
        image_source: Path to image file, URL, or numpy array (from cv2)

    Returns:
        List of detections. Each detection is a dict with 'box', 'confidence', 'label'.

    Raises:
        DetectionException: If pothole detection fails
    """
    try:
        model = get_model()
        if model is None:
            return []

        # perform inference
        # stream=False ensures we get all results in memory
        results = model.predict(image_source, stream=False)

        # observe results
        result = results[0] # Single image

        detections = []

        if hasattr(result, 'boxes'):
            for i, box in enumerate(result.boxes):
                # box.xyxy is [x1, y1, x2, y2] tensor
                # Convert to list
                coords = box.xyxy[0].cpu().numpy().tolist()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                label = result.names[cls_id]

                detections.append({
                    "box": coords, # [x1, y1, x2, y2]
                    "confidence": conf,
                    "label": label
                })

        return detections
    except Exception as e:
        logger.error(f"Pothole detection failed: {e}")
        raise DetectionException("Failed to detect potholes in image", "pothole", details={"error": str(e)}) from e

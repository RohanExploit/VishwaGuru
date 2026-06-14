import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_model = None
_model_lock = threading.Lock()

def load_model():
    """
    Loads the YOLO model lazily.
    """
    logger.info("Loading Garbage Detection Model...")
    try:
        from ultralyticsplus import YOLO
        # Using keremberke/yolov8n-garbage-segmentation as it follows the naming convention
        # of the existing pothole model (keremberke/yolov8n-pothole-segmentation).
        model = YOLO('keremberke/yolov8n-garbage-segmentation')

        model.overrides['conf'] = 0.25
        model.overrides['iou'] = 0.45
        model.overrides['agnostic_nms'] = False
        model.overrides['max_det'] = 1000

        logger.info("Garbage Model loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Failed to load garbage model: {e}")
        return None

def get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:  # Double check inside lock
                _model = load_model()
    return _model

def detect_garbage(image_source):
    """
    Detects garbage in an image.

    Args:
        image_source: Path to image file, URL, or numpy array (from cv2)

    Returns:
        List of detections. Each detection is a dict with 'box', 'confidence', 'label'.
    """
    model = get_model()
    if not model:
        logger.warning("Garbage model not available, returning empty detections.")
        return []

    # perform inference
    try:
        results = model.predict(image_source, stream=False)
        result = results[0] # Single image

        detections = []

        if hasattr(result, 'boxes'):
            for i, box in enumerate(result.boxes):
                coords = box.xyxy[0].cpu().numpy().tolist()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                label = result.names[cls_id]

                detections.append({
                    "box": coords,
                    "confidence": conf,
                    "label": label
                })

        return detections
    except Exception as e:
        logger.error(f"Error during garbage detection inference: {e}")
        return []

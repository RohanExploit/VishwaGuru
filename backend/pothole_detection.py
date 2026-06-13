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
    The model file will be downloaded on the first call if not cached.
    This prevents blocking the application startup.
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
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise e

def get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:  # Double check inside lock
                _model = load_model()
    return _model

def detect_potholes(image_source):
    """
    Detects potholes in an image.

    Args:
        image_source: Path to image file, URL, or numpy array (from cv2)

    Returns:
        List of detections. Each detection is a dict with 'box', 'confidence', 'label'.
    """
    model = get_model()

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

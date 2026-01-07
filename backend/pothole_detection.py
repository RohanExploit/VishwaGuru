import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_model = None

def load_model():
    """Load YOLOv8 pothole model lazily on first use."""
    logger.info("Loading Pothole Detection Model...")
    try:
        # Import here to avoid blocking startup
        from ultralyticsplus import YOLO

        model = YOLO('keremberke/yolov8n-pothole-segmentation')

        # Detection parameters
        model.overrides['conf'] = 0.25
        model.overrides['iou'] = 0.45
        model.overrides['agnostic_nms'] = False
        model.overrides['max_det'] = 1000

        logger.info("Pothole model loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Failed to load pothole model: {e}")
        raise e

def get_model():
    """Get cached model instance. Lazy-loads on first call."""
    global _model
    if _model is None:
        _model = load_model()
    return _model

def detect_potholes(image_source):
    """Detect potholes. Returns list with boxes, confidence, and labels."""
    model = get_model()
    results = model.predict(image_source, stream=False)
    result = results[0]

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

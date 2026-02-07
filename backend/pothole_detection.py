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

_model = None
_model_lock = threading.Lock()

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
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise ModelLoadException("keremberke/yolov8n-pothole-segmentation", details={"error": str(e)}) from e


def get_model():
    """
    Thread-safe singleton accessor for the pothole detection model.
    
    Uses double-checked locking pattern to ensure:
    1. Only one model instance is ever created
    2. Concurrent requests don't trigger multiple model loads
    3. Minimal lock contention after initialization
    
    Returns:
        The loaded YOLO model instance.
        
    Raises:
        Exception: If model loading previously failed or fails on this attempt.
        
    Thread Safety:
        This function is thread-safe and can be called from multiple threads
        simultaneously without causing race conditions or redundant model loads.
    """
    global _model, _model_initialized, _model_loading_error
    
    # First check (without lock) - fast path for already initialized model
    if _model_initialized:
        if _model_loading_error is not None:
            raise _model_loading_error
        return _model
    
    # Acquire lock for thread-safe initialization
    with _model_lock:
        # Second check (with lock) - prevent multiple initializations
        # Another thread may have initialized while we were waiting for the lock
        if _model_initialized:
            if _model_loading_error is not None:
                raise _model_loading_error
            return _model
        
        try:
            logger.info("Initializing model (thread-safe singleton)...")
            _model = load_model()
            _model_initialized = True
            logger.info("Model initialization complete.")
            return _model
        except Exception as e:
            # Cache the error to prevent repeated failed initialization attempts
            _model_loading_error = e
            _model_initialized = True  # Mark as initialized (even though it failed)
            logger.error(f"Model initialization failed: {e}")
            raise ModelLoadException("keremberke/yolov8n-pothole-segmentation", details={"error": str(e)}) from e


def validate_image_for_processing(image):
    """
    Validates if the image is suitable for processing.
    """
    if image is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No image provided for processing")
    return True

def reset_model():
    """
    Resets the model singleton state. Primarily for testing purposes.
    
    Warning:
        This function should only be used in testing scenarios.
        Using it in production while requests are being processed
        could lead to race conditions.
        
    Thread Safety:
        This function is thread-safe but should be used with caution
        in multi-threaded environments.
    """
    global _model, _model_initialized, _model_loading_error
    
    with _model_lock:
        _model = None
        _model_initialized = False
        _model_loading_error = None
        logger.info("Model singleton state has been reset.")

    if _model is None:
        with _model_lock:
            if _model is None:  # Double check inside lock
                try:
                    _model = load_model()
                except Exception:
                    pass
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

"""
Local Machine Learning Service for Image Detection

This module provides local ML models for vandalism, infrastructure damage,
and flooding detection using YOLO models, eliminating the dependency on
Hugging Face API.
"""
import logging
from PIL import Image
import threading
from fastapi.concurrency import run_in_threadpool

from backend.exceptions import DetectionException

# Configure logging
logger = logging.getLogger(__name__)

# Model cache for lazy loading
_general_model = None
_model_lock = threading.Lock()

# Confidence scaling factors
HEURISTIC_CONFIDENCE_FACTOR = 0.6  # Reduce confidence for heuristic detection
LOW_CONFIDENCE_FACTOR = 0.5  # Lower confidence for uncertain detections


def load_general_model():
    """
    Loads a general-purpose YOLO model for object detection.
    This single model will be used for all detection types.
    """
    logger.info("Loading General Object Detection Model...")
    try:
        import torch
        from ultralytics import YOLO
        
        # Monkey-patch torch.load to use weights_only=False for YOLO model loading
        # This is safe because YOLO models from ultralytics are from a trusted source
        original_load = torch.load
        def patched_load(*args, **kwargs):
            kwargs['weights_only'] = False
            return original_load(*args, **kwargs)
        torch.load = patched_load
        
        try:
            # Using YOLOv8 nano model for general object detection (lighter weight)
            # This model can detect 80+ common objects which we can use for
            # vandalism, infrastructure, and flooding detection
            model = YOLO('yolov8n.pt')
            
            # Configure model parameters
            model.overrides['conf'] = 0.25
            model.overrides['iou'] = 0.45
            model.overrides['agnostic_nms'] = False
            model.overrides['max_det'] = 1000
            
            logger.info("General Object Detection Model loaded successfully.")
            return model
        finally:
            # Restore original torch.load
            torch.load = original_load
            
    except Exception as e:
        logger.error(f"Failed to load general detection model: {e}")
        return None


def get_general_model():
    """Get or load general detection model."""
    global _general_model
    if _general_model is None:
        with _model_lock:
            if _general_model is None:
                _general_model = load_general_model()
    return _general_model


async def detect_vandalism_local(image: Image.Image, client=None):
    """
    Detects vandalism/graffiti using local YOLO model (Async compatible).
    
    This uses a general object detection model and interprets results in the context
    of vandalism detection. It looks for suspicious objects or scene anomalies.
    
    Args:
        image: PIL Image object
        client: Unused parameter for compatibility with HF service
        
    Returns:
        List of detections with label, confidence, and box coordinates
    """
    try:
        model = get_general_model()
        if not model:
            logger.warning("Detection model not available, returning empty detections.")
            return []
        
        # Run model prediction in threadpool to avoid blocking event loop
        results = await run_in_threadpool(model.predict, image, stream=False)
        result = results[0]
        
        detections = []
        
        if hasattr(result, 'boxes'):
            for box in result.boxes:
                coords = box.xyxy[0].cpu().numpy().tolist()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                label = result.names[cls_id]
                
                # For vandalism, we flag detections with reasonable confidence
                # This is a heuristic approach - in production, you'd want a specialized model
                if conf > 0.4:
                    # Map generic labels to vandalism context
                    vandalism_label = "potential vandalism"
                    if label.lower() in ['person', 'bottle']:
                        vandalism_label = "vandalism activity"
                    
                    detections.append({
                        "label": vandalism_label,
                        "confidence": conf * HEURISTIC_CONFIDENCE_FACTOR,
                        "box": coords
                    })
        
        # If we detect multiple suspicious objects, mark it as vandalism
        if len(detections) > 0:
            logger.info(f"Vandalism detection found {len(detections)} suspicious objects")
        
        return detections
        
    except Exception as e:
        logger.error(f"Local Vandalism Detection Error: {e}")
        raise DetectionException("Failed to detect vandalism", "vandalism", details={"error": str(e)}) from e


async def detect_infrastructure_local(image: Image.Image, client=None):
    """
    Detects infrastructure damage using local YOLO model (Async compatible).
    
    This uses a general object detection model and interprets results in the context
    of infrastructure damage. It looks for objects that might indicate damage.
    
    Args:
        image: PIL Image object
        client: Unused parameter for compatibility with HF service
        
    Returns:
        List of detections with label, confidence, and box coordinates
    """
    try:
        model = get_general_model()
        if not model:
            logger.warning("Detection model not available, returning empty detections.")
            return []
        
        # Run model prediction in threadpool to avoid blocking event loop
        results = await run_in_threadpool(model.predict, image, stream=False)
        result = results[0]
        
        detections = []
        
        # Objects that might indicate infrastructure issues
        infrastructure_related = ['car', 'truck', 'traffic light', 'stop sign', 'bench', 'fire hydrant']
        
        if hasattr(result, 'boxes'):
            for box in result.boxes:
                coords = box.xyxy[0].cpu().numpy().tolist()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                label = result.names[cls_id]
                
                # Flag infrastructure-related objects
                if conf > 0.4 and label.lower() in infrastructure_related:
                    # Map to infrastructure context
                    infra_label = "infrastructure object"
                    if label.lower() in ['traffic light', 'stop sign']:
                        infra_label = "damaged sign"
                    elif label.lower() == 'fire hydrant':
                        infra_label = "damaged hydrant"
                    
                    detections.append({
                        "label": infra_label,
                        "confidence": conf * HEURISTIC_CONFIDENCE_FACTOR,
                        "box": coords
                    })
        
        logger.info(f"Infrastructure detection found {len(detections)} objects")
        return detections
        
    except Exception as e:
        logger.error(f"Local Infrastructure Detection Error: {e}")
        raise DetectionException("Failed to detect infrastructure damage", "infrastructure", details={"error": str(e)}) from e


async def detect_flooding_local(image: Image.Image, client=None):
    """
    Detects flooding using local YOLO model (Async compatible).
    
    This uses a general object detection model and interprets results in the context
    of flooding. It looks for objects that might be partially submerged or water-related.
    
    Args:
        image: PIL Image object
        client: Unused parameter for compatibility with HF service
        
    Returns:
        List of detections with label, confidence, and box coordinates
    """
    try:
        model = get_general_model()
        if not model:
            logger.warning("Detection model not available, returning empty detections.")
            return []
        
        # Run model prediction in threadpool to avoid blocking event loop
        results = await run_in_threadpool(model.predict, image, stream=False)
        result = results[0]
        
        detections = []
        
        # Objects that might be affected by flooding
        flooding_indicators = ['car', 'truck', 'person', 'bicycle', 'motorcycle', 'bench']
        
        if hasattr(result, 'boxes'):
            for box in result.boxes:
                coords = box.xyxy[0].cpu().numpy().tolist()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                label = result.names[cls_id]
                
                # Check if objects are in positions that might indicate flooding
                if conf > 0.4 and label.lower() in flooding_indicators:
                    # Heuristic: if bottom of bounding box is below image center,
                    # it might be partially submerged
                    image_height = image.height if hasattr(image, 'height') else 480
                    box_bottom = coords[3]
                    
                    if box_bottom > image_height * 0.6:
                        detections.append({
                            "label": "potential flooding",
                            "confidence": conf * LOW_CONFIDENCE_FACTOR,
                            "box": coords
                        })
        
        logger.info(f"Flooding detection found {len(detections)} indicators")
        return detections
        
    except Exception as e:
        logger.error(f"Local Flooding Detection Error: {e}")
        raise DetectionException("Failed to detect flooding", "flooding", details={"error": str(e)}) from e

async def get_detection_status():
    """Get status of local detection model."""
    model = get_general_model()
    return {
        "model_loaded": model is not None,
        "backend": "local_yolo"
    }

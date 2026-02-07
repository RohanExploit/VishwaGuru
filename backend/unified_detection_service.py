"""
Unified Detection Service - Local ML with Optional HF Fallback.

This module provides a unified interface for all civic issue detection,
prioritizing local ML models for offline capability and reduced latency,
with optional fallback to Hugging Face API when needed.

Issue #76: Create a Local Machine Learning model
"""

import os
import logging
from typing import List, Dict, Optional
from PIL import Image
from enum import Enum

from backend.exceptions import DetectionException, ServiceUnavailableException

# Configure logging
logger = logging.getLogger(__name__)

# Configuration: Use local model by default
USE_LOCAL_MODEL = os.environ.get("USE_LOCAL_ML", "true").lower() == "true"
ENABLE_HF_FALLBACK = os.environ.get("ENABLE_HF_FALLBACK", "true").lower() == "true"


class DetectionBackend(Enum):
    """Available detection backends."""
    LOCAL = "local"
    HUGGINGFACE = "huggingface"
    AUTO = "auto"  # Try local first, fallback to HF


class UnifiedDetectionService:
    """
    Unified service for civic issue detection.
    
    This service provides:
    - Automatic backend selection (local or HF API)
    - Graceful fallback when local model fails
    - Consistent interface for all detection types
    - Performance monitoring and logging
    """
    
    def __init__(self, backend: DetectionBackend = DetectionBackend.AUTO):
        self.backend = backend
        self._local_available = None
        self._hf_available = None
    
    async def _check_local_available(self) -> bool:
        """Check if local ML service is available."""
        if self._local_available is not None:
            return self._local_available
        
        try:
            from local_ml_service import get_general_model
            model = get_general_model()
            
            # Check if model is loaded
            if model is None:
                self._local_available = False
                return False

            # Try a simple prediction to verify
            # Run in threadpool as it might be blocking
            from fastapi.concurrency import run_in_threadpool
            test_image = Image.new("RGB", (224, 224), color="white")
            await run_in_threadpool(model.predict, test_image, verbose=False)
            
            self._local_available = True
            return True
            
        except Exception as e:
            logger.warning(f"Local ML service unavailable: {e}")
            self._local_available = False
            return False
    
    async def _check_hf_available(self) -> bool:
        """Check if Hugging Face API is available."""
        if self._hf_available is not None:
            return self._hf_available
        
        try:
            # HF token present indicates API might be available
            token = os.environ.get("HF_TOKEN")
            self._hf_available = True  # Assume available, actual call will verify
            return self._hf_available
        except Exception:
            self._hf_available = False
            return False
    
    async def _get_detection_backend(self) -> str:
        """Determine which backend to use based on configuration and availability."""
        if self.backend == DetectionBackend.LOCAL:
            return "local" if await self._check_local_available() else None
        
        elif self.backend == DetectionBackend.HUGGINGFACE:
            return "huggingface" if await self._check_hf_available() else None
        
        else:  # AUTO
            if USE_LOCAL_MODEL and await self._check_local_available():
                return "local"
            elif ENABLE_HF_FALLBACK and await self._check_hf_available():
                logger.info("Falling back to Hugging Face API")
                return "huggingface"
            else:
                return None
    
    async def detect_vandalism(self, image: Image.Image) -> List[Dict]:
        """
        Detect vandalism in an image.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            List of detections with 'label', 'confidence', and 'box' keys
            
        Raises:
            ServiceUnavailableException: If no detection backend is available
            DetectionException: If detection fails
        """
        backend = await self._get_detection_backend()
        
        if backend == "local":
            from local_ml_service import detect_vandalism_local
            return await detect_vandalism_local(image)
        
        elif backend == "huggingface":
            from hf_service import detect_vandalism_clip
            return await detect_vandalism_clip(image)
        
        else:
            logger.error("No detection backend available")
            raise ServiceUnavailableException("Detection service", details={"detection_type": "vandalism"})
    
    async def detect_infrastructure(self, image: Image.Image) -> List[Dict]:
        """
        Detect infrastructure damage in an image.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            List of detections with 'label', 'confidence', and 'box' keys
            
        Raises:
            ServiceUnavailableException: If no detection backend is available
            DetectionException: If detection fails
        """
        backend = await self._get_detection_backend()
        
        if backend == "local":
            from local_ml_service import detect_infrastructure_local
            return await detect_infrastructure_local(image)
        
        elif backend == "huggingface":
            from hf_service import detect_infrastructure_clip
            return await detect_infrastructure_clip(image)
        
        else:
            logger.error("No detection backend available")
            raise ServiceUnavailableException("Detection service", details={"detection_type": "infrastructure"})
    
    async def detect_flooding(self, image: Image.Image) -> List[Dict]:
        """
        Detect flooding/waterlogging in an image.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            List of detections with 'label', 'confidence', and 'box' keys
            
        Raises:
            ServiceUnavailableException: If no detection backend is available
            DetectionException: If detection fails
        """
        backend = await self._get_detection_backend()
        
        if backend == "local":
            from local_ml_service import detect_flooding_local
            return await detect_flooding_local(image)
        
        elif backend == "huggingface":
            from hf_service import detect_flooding_clip
            return await detect_flooding_clip(image)
        
        else:
            logger.error("No detection backend available")
            raise ServiceUnavailableException("Detection service", details={"detection_type": "flooding"})

    async def detect_garbage(self, image: Image.Image) -> List[Dict]:
        """
        Detect garbage/waste in an image.

        Args:
            image: PIL Image to analyze

        Returns:
            List of detections with 'label', 'confidence', and 'box' keys.
            For HF/CLIP, 'box' will be empty as it classifies the whole image.
        """
        backend = await self._get_detection_backend()

        if backend == "local":
            from backend.garbage_detection import detect_garbage
            # Local model expects image source, but PIL image works if model supports it
            # The existing detect_garbage uses model.predict(image_source)
            # Ultralytics YOLO supports PIL Image directly
            from fastapi.concurrency import run_in_threadpool
            return await run_in_threadpool(detect_garbage, image)

        elif backend == "huggingface":
            from backend.hf_api_service import detect_waste_clip
            result = await detect_waste_clip(image)

            # Map classification to detection format
            if result and result.get("waste_type") != "unknown":
                return [{
                    "label": result["waste_type"],
                    "confidence": result.get("confidence", 0.0),
                    "box": [] # No bounding box for classification
                }]
            return []

        else:
            logger.error("No detection backend available")
            raise ServiceUnavailableException("Detection service", details={"detection_type": "garbage"})
    
    async def detect_all(self, image: Image.Image) -> Dict[str, List[Dict]]:
        """
        Run all detection types on an image.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            Dictionary mapping detection type to list of results
        """
        import asyncio

        results = await asyncio.gather(
            self.detect_vandalism(image),
            self.detect_infrastructure(image),
            self.detect_flooding(image),
            self.detect_garbage(image)
        )

        return {
            "vandalism": results[0],
            "infrastructure": results[1],
            "flooding": results[2],
            "garbage": results[3]
        }
    
    async def get_status(self) -> Dict:
        """
        Get the current status of the detection service.
        
        Returns:
            Dictionary with service status information
        """
        local_available = await self._check_local_available()
        hf_available = await self._check_hf_available()
        
        status = {
            "use_local_model": USE_LOCAL_MODEL,
            "enable_hf_fallback": ENABLE_HF_FALLBACK,
            "local_backend": {
                "available": local_available,
                "status": "ready" if local_available else "unavailable"
            },
            "huggingface_backend": {
                "available": hf_available,
                "status": "ready" if hf_available else "unavailable"
            },
            "active_backend": await self._get_detection_backend()
        }
        
        # Add local model details if available
        if local_available:
            try:
                from local_ml_service import get_detection_status
                status["local_backend"]["details"] = await get_detection_status()
            except Exception:
                pass
        
        return status


# Create a default instance
_default_service = None


def get_detection_service() -> UnifiedDetectionService:
    """Get the default UnifiedDetectionService instance."""
    global _default_service
    if _default_service is None:
        _default_service = UnifiedDetectionService()
    return _default_service


# Convenience functions that use the default service
async def detect_vandalism(image: Image.Image) -> List[Dict]:
    """Detect vandalism using the default service."""
    return await get_detection_service().detect_vandalism(image)


async def detect_infrastructure(image: Image.Image) -> List[Dict]:
    """Detect infrastructure damage using the default service."""
    return await get_detection_service().detect_infrastructure(image)


async def detect_flooding(image: Image.Image) -> List[Dict]:
    """Detect flooding using the default service."""
    return await get_detection_service().detect_flooding(image)


async def detect_garbage(image: Image.Image) -> List[Dict]:
    """Detect garbage using the default service."""
    return await get_detection_service().detect_garbage(image)


async def detect_all(image: Image.Image) -> Dict[str, List[Dict]]:
    """Run all detections using the default service."""
    return await get_detection_service().detect_all(image)


async def get_detection_status() -> Dict:
    """Get detection service status."""
    return await get_detection_service().get_status()

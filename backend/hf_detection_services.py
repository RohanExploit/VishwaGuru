"""
Concrete implementations of detection service interfaces using HuggingFace models.
"""
from typing import List, Dict, Any
from PIL import Image
import httpx
from ai_interfaces import DetectionService
from hf_service import (
    detect_vandalism_clip,
    detect_infrastructure_clip,
    detect_flooding_clip
)


class HFVandalismDetectionService(DetectionService):
    """HuggingFace-based vandalism detection service."""

    async def detect(self, image: Image.Image, client: httpx.AsyncClient = None) -> List[Dict[str, Any]]:
        """Detect vandalism in images using HuggingFace CLIP model."""
        return await detect_vandalism_clip(image, client=client)


class HFInfrastructureDetectionService(DetectionService):
    """HuggingFace-based infrastructure damage detection service."""

    async def detect(self, image: Image.Image, client: httpx.AsyncClient = None) -> List[Dict[str, Any]]:
        """Detect infrastructure damage using HuggingFace CLIP model."""
        return await detect_infrastructure_clip(image, client=client)


class HFFloodingDetectionService(DetectionService):
    """HuggingFace-based flooding detection service."""

    async def detect(self, image: Image.Image, client: httpx.AsyncClient = None) -> List[Dict[str, Any]]:
        """Detect flooding and waterlogging using HuggingFace CLIP model."""
        return await detect_flooding_clip(image, client=client)


class PotholeDetectionService(DetectionService):
    """Local model-based pothole detection service."""

    async def detect(self, image: Image.Image, client: Any = None) -> List[Dict[str, Any]]:
        """Detect potholes using local detection model."""
        from pothole_detection import detect_potholes
        import asyncio
        # Run blocking detection in threadpool
        return await asyncio.to_thread(detect_potholes, image)


class GarbageDetectionService(DetectionService):
    """Local model-based garbage detection service."""

    async def detect(self, image: Image.Image, client: Any = None) -> List[Dict[str, Any]]:
        """Detect garbage using local detection model."""
        from garbage_detection import detect_garbage
        import asyncio
        # Run blocking detection in threadpool
        return await asyncio.to_thread(detect_garbage, image)


# Factory functions for easy service creation
def create_hf_vandalism_detection_service() -> HFVandalismDetectionService:
    """Create a HuggingFace-based vandalism detection service."""
    return HFVandalismDetectionService()


def create_hf_infrastructure_detection_service() -> HFInfrastructureDetectionService:
    """Create a HuggingFace-based infrastructure detection service."""
    return HFInfrastructureDetectionService()


def create_hf_flooding_detection_service() -> HFFloodingDetectionService:
    """Create a HuggingFace-based flooding detection service."""
    return HFFloodingDetectionService()


def create_local_pothole_detection_service() -> PotholeDetectionService:
    """Create a local pothole detection service."""
    return PotholeDetectionService()


def create_local_garbage_detection_service() -> GarbageDetectionService:
    """Create a local garbage detection service."""
    return GarbageDetectionService()

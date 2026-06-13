"""
Mock implementations of detection service interfaces for testing and development.
"""
from typing import List, Dict, Any
import asyncio
from ai_interfaces import DetectionService


class MockDetectionService(DetectionService):
    """Base mock detection service with configurable responses."""

    def __init__(self, detection_label: str = "mock_detection"):
        self.detection_label = detection_label

    async def detect(self, image: Any, client: Any = None) -> List[Dict[str, Any]]:
        """Return a mock detection result."""
        await asyncio.sleep(0.1)  # Simulate async operation
        return [
            {
                "label": self.detection_label,
                "confidence": 0.85,
                "box": [10, 20, 100, 120]
            }
        ]


class MockVandalismDetectionService(MockDetectionService):
    """Mock vandalism detection service."""

    def __init__(self):
        super().__init__(detection_label="graffiti")


class MockInfrastructureDetectionService(MockDetectionService):
    """Mock infrastructure damage detection service."""

    def __init__(self):
        super().__init__(detection_label="broken streetlight")


class MockFloodingDetectionService(MockDetectionService):
    """Mock flooding detection service."""

    def __init__(self):
        super().__init__(detection_label="flooded street")


class MockPotholeDetectionService(MockDetectionService):
    """Mock pothole detection service."""

    def __init__(self):
        super().__init__(detection_label="pothole")


class MockGarbageDetectionService(MockDetectionService):
    """Mock garbage detection service."""

    def __init__(self):
        super().__init__(detection_label="garbage pile")


# Factory functions for easy service creation
def create_mock_vandalism_detection_service() -> MockVandalismDetectionService:
    """Create a mock vandalism detection service."""
    return MockVandalismDetectionService()


def create_mock_infrastructure_detection_service() -> MockInfrastructureDetectionService:
    """Create a mock infrastructure detection service."""
    return MockInfrastructureDetectionService()


def create_mock_flooding_detection_service() -> MockFloodingDetectionService:
    """Create a mock flooding detection service."""
    return MockFloodingDetectionService()


def create_mock_pothole_detection_service() -> MockPotholeDetectionService:
    """Create a mock pothole detection service."""
    return MockPotholeDetectionService()


def create_mock_garbage_detection_service() -> MockGarbageDetectionService:
    """Create a mock garbage detection service."""
    return MockGarbageDetectionService()

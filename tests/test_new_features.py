import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from backend.main import app

# Ensure main uses the correct router if it imports it directly,
# but usually it imports from backend.routers.detection which we modified.
# We need to make sure the app instance reflects the changes.
# Since we modified the files on disk, and TestClient imports app, it should be fine.

# Context manager for startup/shutdown events
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.mark.asyncio
async def test_detect_public_facilities_endpoint(client):
    # Mock the HF service function
    with patch("backend.routers.detection.detect_public_facilities_clip", new_callable=AsyncMock) as mock_detect:
        mock_detect.return_value = [{"label": "broken bench", "confidence": 0.95, "box": []}]

        # Create a dummy image file
        files = {"image": ("test.jpg", b"fakeimagebytes", "image/jpeg")}

        response = client.post("/api/detect-public-facilities", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
        assert len(data["detections"]) == 1
        assert data["detections"][0]["label"] == "broken bench"

@pytest.mark.asyncio
async def test_detect_construction_safety_endpoint(client):
    # Mock the HF service function
    with patch("backend.routers.detection.detect_construction_safety_clip", new_callable=AsyncMock) as mock_detect:
        mock_detect.return_value = [{"label": "missing barrier", "confidence": 0.88, "box": []}]

        # Create a dummy image file
        files = {"image": ("test.jpg", b"fakeimagebytes", "image/jpeg")}

        response = client.post("/api/detect-construction-safety", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
        assert len(data["detections"]) == 1
        assert data["detections"][0]["label"] == "missing barrier"

from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.main import app
import pytest
import io
from PIL import Image

client = TestClient(app)

@pytest.fixture
def mock_detect_graffiti():
    # Patch where it is imported in backend.routers.detection
    with patch("backend.routers.detection.detect_graffiti_art_clip") as mock:
        yield mock

@pytest.fixture
def mock_process_image():
    with patch("backend.routers.detection.process_uploaded_image") as mock:
        yield mock

def test_detect_graffiti(mock_detect_graffiti, mock_process_image):
    # Mock return value
    mock_process.return_value = (None, b"fake_image_bytes")
    mock_detect_graffiti.return_value = [
        {"label": "street art", "confidence": 0.95, "box": []},
        {"label": "clean wall", "confidence": 0.05, "box": []}
    ]

    mock_process_image.return_value = ("test.jpg", b"fake_image_bytes")

    # Simple dummy bytes
    files = {"image": ("test.jpg", b"fake_image_bytes", "image/jpeg")}

    response = client.post("/api/detect-graffiti", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) == 2
    assert data["detections"][0]["label"] == "street art"

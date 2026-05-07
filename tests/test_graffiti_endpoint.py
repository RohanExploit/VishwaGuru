from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.main import app
import pytest

client = TestClient(app)

@pytest.fixture
def mock_detect_graffiti():
    # Patch where it is imported in backend.routers.detection
    with patch("backend.routers.detection.detect_graffiti_art_clip") as mock:
        yield mock

@pytest.fixture
def mock_validate_file():
    with patch("backend.routers.detection.validate_uploaded_file") as mock:
        yield mock

@patch("backend.routers.detection.process_uploaded_image", new_callable=AsyncMock)
def test_detect_graffiti(mock_process, mock_detect_graffiti, mock_validate_file):
    # Mock return value
    mock_process.return_value = (None, b"fake_image_bytes")
    mock_detect_graffiti.return_value = [
        {"label": "street art", "confidence": 0.95, "box": []},
        {"label": "clean wall", "confidence": 0.05, "box": []}
    ]

    # Simple dummy bytes
    files = {"image": ("test.jpg", b"fake_image_bytes", "image/jpeg")}

    response = client.post("/api/detect-graffiti", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) == 2
    assert data["detections"][0]["label"] == "street art"

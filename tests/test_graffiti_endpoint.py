from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.main import app
import pytest
from io import BytesIO
from PIL import Image

client = TestClient(app)

@pytest.fixture
def mock_detect_graffiti():
    # Patch where it is imported in backend.routers.detection
    with patch("backend.routers.detection._cached_detect_graffiti", new_callable=AsyncMock) as mock:
        yield mock

@pytest.fixture
def mock_validate_file():
    with patch("backend.routers.detection.validate_uploaded_file") as mock:
        yield mock

def test_detect_graffiti(mock_detect_graffiti, mock_validate_file):
    # Mock return value
    mock_detect_graffiti.return_value = [
        {"label": "street art", "confidence": 0.95, "box": []},
        {"label": "clean wall", "confidence": 0.05, "box": []}
    ]

    # Simple dummy bytes
    img = Image.new('RGB', (100, 100))
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    file_content = img_bytes.getvalue()

    files = {"image": ("test.jpg", file_content, "image/jpeg")}

    response = client.post("/api/detect-graffiti", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) == 2
    assert data["detections"][0]["label"] == "street art"

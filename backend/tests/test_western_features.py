import sys
from unittest.mock import MagicMock

# Mock heavy dependencies
sys.modules["ultralytics"] = MagicMock()
sys.modules["ultralyticsplus"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["telegram"] = MagicMock()
sys.modules["telegram.ext"] = MagicMock()
sys.modules["telegram.error"] = MagicMock()
sys.modules["pywebpush"] = MagicMock()
sys.modules["firebase_admin"] = MagicMock()
sys.modules["firebase_admin.credentials"] = MagicMock()
sys.modules["firebase_admin.firestore"] = MagicMock()

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
import io
from PIL import Image

# Import app after mocking
from backend.main import app

@pytest.fixture
def mock_image():
    file = io.BytesIO()
    image = Image.new("RGB", (100, 100), color="white")
    image.save(file, format="JPEG")
    file.seek(0)
    return file

@pytest.mark.asyncio
async def test_detect_public_transport_endpoint(mock_image):
    with patch("backend.hf_api_service._make_request") as mock_request, \
         patch("backend.routers.detection.get_http_client") as mock_get_client:
        # Mock HF API response for CLIP
        mock_request.return_value = [
            {"label": "damaged bus stop", "score": 0.95},
            {"label": "safe waiting area", "score": 0.05}
        ]
        mock_get_client.return_value = MagicMock()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            files = {"image": ("test.jpg", mock_image, "image/jpeg")}
            response = await ac.post("/api/detect-public-transport", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
        assert len(data["detections"]) > 0
        assert data["detections"][0]["label"] == "damaged bus stop"

@pytest.mark.asyncio
async def test_detect_cleanliness_endpoint(mock_image):
    with patch("backend.hf_api_service._make_request") as mock_request, \
         patch("backend.routers.detection.get_http_client") as mock_get_client:
        mock_request.return_value = [
            {"label": "garbage overflow", "score": 0.85},
            {"label": "clean area", "score": 0.15}
        ]
        mock_get_client.return_value = MagicMock()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            files = {"image": ("test.jpg", mock_image, "image/jpeg")}
            response = await ac.post("/api/detect-cleanliness", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
        assert len(data["detections"]) > 0
        assert data["detections"][0]["label"] == "garbage overflow"

@pytest.mark.asyncio
async def test_detect_playground_endpoint(mock_image):
    with patch("backend.hf_api_service._make_request") as mock_request, \
         patch("backend.routers.detection.get_http_client") as mock_get_client:
        mock_request.return_value = [
            {"label": "rusted slide", "score": 0.92},
            {"label": "safe playground", "score": 0.08}
        ]
        mock_get_client.return_value = MagicMock()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            files = {"image": ("test.jpg", mock_image, "image/jpeg")}
            response = await ac.post("/api/detect-playground", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
        assert len(data["detections"]) > 0
        assert data["detections"][0]["label"] == "rusted slide"

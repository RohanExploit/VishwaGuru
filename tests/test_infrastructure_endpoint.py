from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch, MagicMock, AsyncMock
from PIL import Image
import io
import pytest

# Use context manager to trigger lifespan events (initializing http_client)
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@patch("backend.main.detect_infrastructure_local", new_callable=AsyncMock)
@patch("backend.main.run_in_threadpool")
def test_detect_infrastructure_endpoint(mock_run, mock_detect, client):
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    # Mock Image.open calls via run_in_threadpool
    async def async_mock_run_img(*args, **kwargs):
        if args[0] == Image.open:
            return img
        return MagicMock() # Fallback

    mock_run.side_effect = async_mock_run_img

    mock_detect.return_value = [{"label": "broken streetlight", "confidence": 0.95, "box": []}]

    response = client.post(
        "/api/detect-infrastructure",
        files={"image": ("test.jpg", img_byte_arr, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) == 1
    assert data["detections"][0]["label"] == "broken streetlight"

@patch("backend.main.detect_infrastructure_local", new_callable=AsyncMock)
@patch("backend.main.run_in_threadpool")
def test_detect_infrastructure_endpoint_empty(mock_run, mock_detect, client):
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    # Mock Image.open calls via run_in_threadpool
    async def async_mock_run_img(*args, **kwargs):
        if args[0] == Image.open:
            return img
        return MagicMock() # Fallback

    mock_run.side_effect = async_mock_run_img

    # Mock the detection function to return empty list
    mock_detect.return_value = []

    response = client.post(
        "/api/detect-infrastructure",
        files={"image": ("test.jpg", img_byte_arr, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) == 0

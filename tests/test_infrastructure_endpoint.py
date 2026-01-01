from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch, MagicMock
from PIL import Image
import io

client = TestClient(app)

def test_detect_infrastructure_endpoint():
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    # Mock the detection function
    # Note: backend.main imports detect_infrastructure from infrastructure_detection
    # and we need to mock it where it is used or imported.
    # Since main.py imports it: `from infrastructure_detection import detect_infrastructure`
    # We should patch 'backend.main.detect_infrastructure' OR 'backend.infrastructure_detection.detect_infrastructure' depending on how it's used.
    # But wait, run_in_threadpool(detect_infrastructure, ...) uses the function object.
    # Let's try patching where it is defined, but ensure the patch is applied before the import if possible, or patch the object in main.

    with patch('backend.main.detect_infrastructure') as mock_detect:
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

def test_detect_infrastructure_endpoint_empty():
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    # Mock the detection function to return empty list
    with patch('backend.main.detect_infrastructure') as mock_detect:
        mock_detect.return_value = []

        response = client.post(
            "/api/detect-infrastructure",
            files={"image": ("test.jpg", img_byte_arr, "image/jpeg")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
        assert len(data["detections"]) == 0

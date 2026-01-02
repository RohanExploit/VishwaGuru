from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app
from PIL import Image
import io

client = TestClient(app)

def create_dummy_image():
    # Create a small dummy image for testing
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

@patch("backend.main.detect_fire")
def test_detect_fire_endpoint(mock_detect_fire):
    # Mock the detection function
    mock_detect_fire.return_value = [{"label": "fire", "confidence": 0.95, "box": []}]

    img_bytes = create_dummy_image()
    response = client.post(
        "/api/detect-fire",
        files={"image": ("test.jpg", img_bytes, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert data["detections"][0]["label"] == "fire"
    mock_detect_fire.assert_called_once()

@patch("backend.main.detect_stray_animal")
def test_detect_stray_animal_endpoint(mock_detect_stray):
    # Mock the detection function
    mock_detect_stray.return_value = [{"label": "stray dog", "confidence": 0.88, "box": []}]

    img_bytes = create_dummy_image()
    response = client.post(
        "/api/detect-stray-animal",
        files={"image": ("test.jpg", img_bytes, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert data["detections"][0]["label"] == "stray dog"
    mock_detect_stray.assert_called_once()

from fastapi.testclient import TestClient
from backend.main import app
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

client = TestClient(app)

@patch("backend.main.detect_traffic_violation_clip", new_callable=AsyncMock)
@patch("backend.main.run_in_threadpool")
@patch("backend.main.Image.open")
def test_detect_traffic(mock_image_open, mock_run, mock_detect_traffic):
    # Mock Image.open to return a valid object (mock)
    mock_image = MagicMock()
    mock_image_open.return_value = mock_image

    # Mock image content
    image_content = b"fakeimagecontent"

    # Mock result
    mock_result = [{"label": "illegal parking", "confidence": 0.88, "box": []}]
    mock_detect_traffic.return_value = mock_result

    async def async_mock_run_img(*args, **kwargs):
        return mock_image

    mock_run.side_effect = async_mock_run_img

    response = client.post(
        "/api/detect-traffic",
        files={"image": ("test.jpg", image_content, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert data["detections"][0]["label"] == "illegal parking"
    assert data["detections"][0]["confidence"] == 0.88

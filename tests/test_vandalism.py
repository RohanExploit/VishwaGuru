from fastapi.testclient import TestClient
from backend.main import app
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Use TestClient with a context manager to ensure lifespan events run
# However, TestClient(app) doesn't run lifespan by default in older versions,
# but in recent Starlette/FastAPI it does if used as context manager.
# Alternatively, we can manually mock app.state.

client = TestClient(app)

def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    json_response = response.json()
    assert "data" in json_response
    assert json_response["data"]["service"] == "VishwaGuru API"

@patch("backend.main.magic.from_buffer")
@patch("backend.main.detect_vandalism_local", new_callable=AsyncMock)
@patch("backend.main.run_in_threadpool")
@patch("backend.main.Image.open")
def test_detect_vandalism(mock_image_open, mock_run, mock_detect_vandalism, mock_magic, client):
    # Mock magic to return image/jpeg
    mock_magic.return_value = "image/jpeg"

    # Mock Image.open to return a valid object (mock)
    mock_image = MagicMock()
    mock_image_open.return_value = mock_image

    # Mock image content
    image_content = b"fakeimagecontent"

    # Mock result
    mock_result = [{"label": "graffiti", "confidence": 0.95, "box": []}]
    mock_detect_vandalism.return_value = mock_result

    # Note: run_in_threadpool is still used for Image.open, so we mock it
    # But for detection it is NOT used.
    async def async_mock_run_img(*args, **kwargs):
        return mock_image

    mock_run.side_effect = async_mock_run_img

    # Use client as context manager to trigger lifespan events
    with TestClient(app) as client:
        response = client.post(
            "/api/detect-vandalism",
            files={"image": ("test.jpg", image_content, "image/jpeg")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
        assert data["detections"][0]["label"] == "graffiti"

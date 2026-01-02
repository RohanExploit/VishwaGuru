from fastapi.testclient import TestClient
from backend.main import app
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "VishwaGuru API"

@patch("backend.main.detect_vandalism_clip")
@patch("backend.main.run_in_threadpool")
@patch("backend.main.Image.open")
def test_detect_vandalism(mock_image_open, mock_run, mock_detect):
    # Mock authentication

    # Mock Image.open to return a valid object (mock)
    mock_image = MagicMock()
    mock_image_open.return_value = mock_image

    # Mock image content
    image_content = b"fakeimagecontent"

    # Mock result
    mock_result = [{"label": "graffiti", "confidence": 0.95, "box": []}]

    # Setup async mock for detect_vandalism_clip
    mock_detect.return_value = mock_result
    mock_detect.side_effect = None # Ensure it returns the value, not a coroutine unless AsyncMock does it automatically

    # If mock_detect is a standard Mock, we need to make it behave like an async function if it's awaited
    # However, since we patched it, we can just use AsyncMock or set return_value
    # But wait, patch doesn't automatically make it AsyncMock unless spec=True/new_callable=AsyncMock
    # Let's fix the test to use AsyncMock or set return_value properly for await

    # Actually, the easier way for async functions is usually setting return_value to the result
    # if the code awaits it, the mock object needs to be awaitable? No, AsyncMock is.

    # Re-patching with AsyncMock in the decorator is cleaner but let's just do it manually here if needed
    # But for now, let's assume we change the patch to target the new function name `detect_vandalism_clip`
    pass

# We rewrite the test completely to be cleaner
@patch("backend.main.detect_vandalism_clip", new_callable=AsyncMock)
@patch("backend.main.run_in_threadpool")
@patch("backend.main.Image.open")
def test_detect_vandalism_new(mock_image_open, mock_run, mock_detect_vandalism):
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

    response = client.post(
        "/api/detect-vandalism",
        files={"image": ("test.jpg", image_content, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert data["detections"][0]["label"] == "graffiti"

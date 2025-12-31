from fastapi.testclient import TestClient
from backend.main import app
import os
import pytest
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "VishwaGuru API"

@patch("backend.main.detect_vandalism")
@patch("backend.main.run_in_threadpool")
@patch("PIL.Image.open")
def test_detect_vandalism(mock_image_open, mock_run, mock_detect):
    # Mock authentication

    # Mock Image.open to return a valid object (mock)
    mock_image = MagicMock()
    mock_image_open.return_value = mock_image

    # Mock image content
    image_content = b"fakeimagecontent"

    # Mock result
    mock_result = [{"label": "graffiti", "confidence": 0.95, "box": []}]

    # Setup async mock for run_in_threadpool
    async def async_mock_run(*args, **kwargs):
        return mock_result

    mock_run.side_effect = async_mock_run

    response = client.post(
        "/api/detect-vandalism",
        files={"file": ("test.jpg", image_content, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert data["detections"][0]["label"] == "graffiti"

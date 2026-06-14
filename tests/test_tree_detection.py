
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Ensure backend path is in sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import app

@pytest.fixture
def client():
    # Mock the shared HTTP client to avoid actual network calls
    app.state.http_client = AsyncMock()
    with TestClient(app) as client:
        yield client

def test_detect_tree_hazard(client):
    # Mock the detect_tree_clip function in main.py
    with patch("main.detect_tree_clip", new_callable=AsyncMock) as mock_detect:
        # Define what the mock should return
        mock_detect.return_value = [
            {"label": "fallen tree", "confidence": 0.9, "box": []}
        ]

        # Create a dummy image file
        file_content = b"fake image content"
        files = {"image": ("test.jpg", file_content, "image/jpeg")}

        # Since we are mocking detect_tree_clip, we also need to ensure PIL doesn't fail
        # but the endpoint calls run_in_threadpool(Image.open, ...), so we should mock Image.open
        with patch("PIL.Image.open") as mock_open:
            mock_open.return_value = MagicMock() # Mock image object

            response = client.post("/api/detect-tree-hazard", files=files)

            assert response.status_code == 200
            data = response.json()
            assert "detections" in data
            assert len(data["detections"]) == 1
            assert data["detections"][0]["label"] == "fallen tree"
            assert data["detections"][0]["confidence"] == 0.9

def test_detect_tree_hazard_no_hazard(client):
     with patch("main.detect_tree_clip", new_callable=AsyncMock) as mock_detect:
        # Return empty list (no hazard detected)
        mock_detect.return_value = []

        with patch("PIL.Image.open") as mock_open:
            mock_open.return_value = MagicMock()

            files = {"image": ("test.jpg", b"fake", "image/jpeg")}
            response = client.post("/api/detect-tree-hazard", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["detections"] == []

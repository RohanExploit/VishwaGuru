import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
import sys
import os

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

# Mock modules before importing main
# We need to mock 'bot' specifically because it might try to start things
sys.modules['backend.bot'] = MagicMock()

# Import app after mocking
# Note: We must import from backend.main, not just main, to avoid double loading
from backend.main import app

# Create a client that runs the lifespan events (startup/shutdown)
# This ensures app.state.http_client is initialized
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.mark.asyncio
async def test_detect_tree_hazard_endpoint(client):
    # Mock the HF service function
    # Note: We patch 'backend.main.detect_tree_hazard_clip' because that's where it's imported in main.py
    with patch('backend.main.detect_tree_hazard_clip', new_callable=AsyncMock) as mock_detect:
        mock_detect.return_value = [{"label": "fallen tree", "confidence": 0.9, "box": []}]

        # Create a mock image file
        file_content = b"fakeimagebytes"

        response = client.post(
            "/api/detect-tree-hazard",
            files={"image": ("test.jpg", file_content, "image/jpeg")}
        )

        assert response.status_code == 200
        assert response.json() == {"detections": [{"label": "fallen tree", "confidence": 0.9, "box": []}]}

@pytest.mark.asyncio
async def test_detect_pest_endpoint(client):
    # Mock the HF service function
    with patch('backend.main.detect_pest_clip', new_callable=AsyncMock) as mock_detect:
        mock_detect.return_value = [{"label": "rat", "confidence": 0.85, "box": []}]

        file_content = b"fakeimagebytes"

        response = client.post(
            "/api/detect-pest",
            files={"image": ("test.jpg", file_content, "image/jpeg")}
        )

        assert response.status_code == 200
        assert response.json() == {"detections": [{"label": "rat", "confidence": 0.85, "box": []}]}

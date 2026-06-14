
import sys
import os
import io
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from PIL import Image

# Ensure backend path is in sys.path
sys.path.append(os.getcwd())

# Mock external heavy dependencies
sys.modules['ultralytics'] = MagicMock()
sys.modules['ultralyticsplus'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['telegram'] = MagicMock()
sys.modules['telegram.ext'] = MagicMock()
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_functions'] = MagicMock()

# Mock internal modules that cause side effects during import
mock_db = MagicMock()
sys.modules['backend.database'] = mock_db
sys.modules['backend.init_db'] = MagicMock()
sys.modules['backend.ai_factory'] = MagicMock()
sys.modules['backend.ai_interfaces'] = MagicMock()
sys.modules['backend.bot'] = MagicMock()
sys.modules['backend.maharashtra_locator'] = MagicMock()
sys.modules['backend.grievance_service'] = MagicMock()

# Mock backend.models.Issue as a class to satisfy typing
class MockIssue:
    pass

class MockPushSubscription:
    pass

mock_models = MagicMock()
mock_models.Issue = MockIssue
mock_models.PushSubscription = MockPushSubscription
sys.modules['backend.models'] = mock_models

# Use environment variable to avoid FRONTEND_URL error
os.environ["FRONTEND_URL"] = "http://localhost:5173"

# We need to ensure backend.main can be imported
try:
    from backend.main import app
except Exception as e:
    # If import fails, we might need to debug what dependency is missing
    print(f"Failed to import app: {e}")
    raise e

from backend.hf_api_service import (
    detect_air_quality_clip,
    detect_playground_clip,
    detect_public_transport_clip,
    detect_cleanliness_verification_clip
)

# Create client and set up state
client = TestClient(app)
app.state.http_client = AsyncMock()

def create_test_image():
    img = Image.new('RGB', (100, 100), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

@pytest.mark.asyncio
async def test_detect_air_quality():
    # Mock the HF API response
    with patch('backend.hf_api_service.query_hf_api', new_callable=AsyncMock) as mock_query:
        # Simulate smog detection
        mock_query.return_value = [
            {"label": "smog", "score": 0.95},
            {"label": "clear sky", "score": 0.05}
        ]

        img_bytes = create_test_image()
        response = client.post(
            "/api/detect-air-quality",
            files={"image": ("smog.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
        assert len(data["detections"]) > 0
        assert data["detections"][0]["label"] == "smog"

@pytest.mark.asyncio
async def test_detect_playground():
    with patch('backend.hf_api_service.query_hf_api', new_callable=AsyncMock) as mock_query:
        # Simulate broken swing
        mock_query.return_value = [
            {"label": "broken swing", "score": 0.88},
            {"label": "safe playground", "score": 0.12}
        ]

        img_bytes = create_test_image()
        response = client.post(
            "/api/detect-playground",
            files={"image": ("playground.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["detections"][0]["label"] == "broken swing"

@pytest.mark.asyncio
async def test_detect_public_transport():
    with patch('backend.hf_api_service.query_hf_api', new_callable=AsyncMock) as mock_query:
        # Simulate damaged bus stop
        mock_query.return_value = [
            {"label": "damaged bus stop", "score": 0.91},
            {"label": "clean bus stop", "score": 0.09}
        ]

        img_bytes = create_test_image()
        response = client.post(
            "/api/detect-public-transport",
            files={"image": ("bus_stop.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["detections"][0]["label"] == "damaged bus stop"

@pytest.mark.asyncio
async def test_detect_cleanliness():
    with patch('backend.hf_api_service.query_hf_api', new_callable=AsyncMock) as mock_query:
        # Simulate dirty street
        mock_query.return_value = [
            {"label": "dirty street", "score": 0.85},
            {"label": "clean street", "score": 0.15}
        ]

        img_bytes = create_test_image()
        response = client.post(
            "/api/detect-cleanliness",
            files={"image": ("street.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["detections"][0]["label"] == "dirty street"

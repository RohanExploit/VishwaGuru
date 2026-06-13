
import pytest
import warnings
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
import io
import sys
import os
from PIL import Image

# Suppress warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
from pathlib import Path

# Ensure repository root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set environment variable
os.environ['FRONTEND_URL'] = 'http://localhost:5173'

# Mock magic
mock_magic = MagicMock()
mock_magic.from_buffer.return_value = "image/jpeg"
sys.modules['magic'] = mock_magic

# Mock telegram
mock_telegram = MagicMock()
sys.modules['telegram'] = mock_telegram
sys.modules['telegram.ext'] = mock_telegram.ext

# Mock create_all_ai_services in main
with patch("backend.main.create_all_ai_services") as mock_create_ai:
    mock_action = AsyncMock()
    mock_chat = AsyncMock()
    mock_summary = AsyncMock()
    mock_create_ai.return_value = (mock_action, mock_chat, mock_summary)
    from backend.main import app

@pytest.fixture
def client():
    mock_client = AsyncMock()
    # Patch get_http_client in detection router to return our mock
    with patch("backend.routers.detection.get_http_client", return_value=mock_client):
         with TestClient(app) as c:
            c.app.state.http_client = mock_client
            yield c

def create_test_image():
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

@pytest.mark.asyncio
async def test_detect_traffic_sign_damaged(client):
    img_bytes = create_test_image()

    with patch('backend.utils.process_uploaded_image', AsyncMock(return_value=(MagicMock(), img_bytes))), \
         patch('backend.routers.detection._cached_detect_traffic_sign', AsyncMock(return_value=[{"label": "damaged traffic sign", "score": 0.95}])):
        response = client.post(
            "/api/detect-traffic-sign",
            files={"image": ("sign.jpg", img_bytes, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) == 1
    assert data["detections"][0]["label"] == "damaged traffic sign"

@pytest.mark.asyncio
async def test_detect_traffic_sign_clear(client):
    img_bytes = create_test_image()

    with patch('backend.utils.process_uploaded_image', AsyncMock(return_value=(MagicMock(), img_bytes))), \
         patch('backend.routers.detection._cached_detect_traffic_sign', AsyncMock(return_value=[])):
        response = client.post(
            "/api/detect-traffic-sign",
            files={"image": ("sign.jpg", img_bytes, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    # Should be empty because 'clear traffic sign' is not in targets
    assert len(data["detections"]) == 0

@pytest.mark.asyncio
async def test_detect_abandoned_vehicle_found(client):
    img_bytes = create_test_image()

    with patch('backend.utils.process_uploaded_image', AsyncMock(return_value=(MagicMock(), img_bytes))), \
         patch('backend.routers.detection._cached_detect_abandoned_vehicle', AsyncMock(return_value=[{"label": "abandoned car", "score": 0.92}])):
        response = client.post(
            "/api/detect-abandoned-vehicle",
            files={"image": ("car.jpg", img_bytes, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["detections"]) == 1
    assert data["detections"][0]["label"] == "abandoned car"


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

import backend.main
from backend.main import app

@pytest.fixture
def client():
    import backend.main as b_main
    import backend.dependencies
    # Patch create_all_ai_services to prevent failing initialization
    with patch.object(b_main, "create_all_ai_services") as mock_create:
         mock_create.return_value = (AsyncMock(), AsyncMock(), AsyncMock())
         mock_client = AsyncMock()
         # Patch httpx.AsyncClient to return our mock to handle lifespan properly
         with patch("httpx.AsyncClient", return_value=mock_client):
             with TestClient(app) as c:
                c.app.state.http_client = mock_client
                import backend.dependencies
                backend.dependencies.SHARED_HTTP_CLIENT = mock_client
                yield c

def create_test_image():
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

@pytest.mark.asyncio
async def test_detect_traffic_sign_damaged(client):
    # Mock the HF API response at the lower level (_make_request or query_hf_api)
    # Since we are mocking the client, we mock the client.post response

    mock_http_client = client.app.state.http_client
    mock_response = MagicMock()
    mock_response.status_code = 200
    # CLIP response is a list of dicts
    mock_response.json.return_value = [
        {"label": "damaged traffic sign", "score": 0.95},
        {"label": "clear traffic sign", "score": 0.05}
    ]
    mock_http_client.post.return_value = mock_response

    img_bytes = create_test_image()

    with patch('backend.utils.validate_uploaded_file'), \
         patch('backend.routers.detection._get_cached_result', AsyncMock(return_value=[{"label": "damaged traffic sign", "confidence": 0.95, "box": []}])):
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

    with patch('backend.utils.validate_uploaded_file'), \
         patch('backend.routers.detection._get_cached_result', AsyncMock(return_value=[])):
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

    with patch('backend.utils.validate_uploaded_file'), \
         patch('backend.routers.detection._get_cached_result', AsyncMock(return_value=[{"label": "abandoned car", "confidence": 0.92, "box": []}])):
        response = client.post(
            "/api/detect-abandoned-vehicle",
            files={"image": ("car.jpg", img_bytes, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["detections"]) == 1
    assert data["detections"][0]["label"] == "abandoned car"

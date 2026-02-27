
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
# We need to mock backend.main specifically because that's where the import is failing or the patch target is
# The previous error "AttributeError: module 'backend' has no attribute 'main'" suggests backend.main wasn't imported yet
# or the patch target string is resolving incorrectly in the test context.

# Let's try importing main first inside the patch context or just import app if possible
# But importing app will trigger lifespan and side effects.

# Alternative: Mock the router dependencies directly without importing full main app if possible,
# but we need the app instance for TestClient.

# Let's try to patch where 'create_all_ai_services' is defined, or imported.
# It is defined in backend.ai_factory.
# But main.py calls it.

@pytest.fixture
def client():
    # We need to successfully import backend.main to get 'app'
    # We will wrap the import in a patch context to mock side effects

    with patch("backend.ai_factory.create_all_ai_services") as mock_create:
        mock_action = AsyncMock()
        mock_chat = AsyncMock()
        mock_summary = AsyncMock()
        mock_create.return_value = (mock_action, mock_chat, mock_summary)

        from backend.main import app

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

    with patch('backend.utils.validate_uploaded_file'):
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
    mock_http_client = client.app.state.http_client
    mock_response = MagicMock()
    mock_response.status_code = 200
    # CLIP response: top is clear
    mock_response.json.return_value = [
        {"label": "clear traffic sign", "score": 0.95},
        {"label": "damaged traffic sign", "score": 0.05}
    ]
    mock_http_client.post.return_value = mock_response

    img_bytes = create_test_image()

    with patch('backend.utils.validate_uploaded_file'):
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
    mock_http_client = client.app.state.http_client
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"label": "abandoned car", "score": 0.92},
        {"label": "normal parked car", "score": 0.08}
    ]
    mock_http_client.post.return_value = mock_response

    img_bytes = create_test_image()

    with patch('backend.utils.validate_uploaded_file'):
        response = client.post(
            "/api/detect-abandoned-vehicle",
            files={"image": ("car.jpg", img_bytes, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["detections"]) == 1
    assert data["detections"][0]["label"] == "abandoned car"

@pytest.mark.asyncio
async def test_detect_construction_safety(client):
    mock_http_client = client.app.state.http_client
    mock_response = MagicMock()
    mock_response.status_code = 200
    # CLIP response: detecting "worker without helmet"
    mock_response.json.return_value = [
        {"label": "worker without helmet", "score": 0.95},
        {"label": "safe construction", "score": 0.05}
    ]
    mock_http_client.post.return_value = mock_response

    img_bytes = create_test_image()

    with patch('backend.utils.validate_uploaded_file'):
        response = client.post(
            "/api/detect-construction-safety",
            files={"image": ("site.jpg", img_bytes, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) == 1
    assert data["detections"][0]["label"] == "worker without helmet"

@pytest.mark.asyncio
async def test_detect_playground_damage(client):
    mock_http_client = client.app.state.http_client
    mock_response = MagicMock()
    mock_response.status_code = 200
    # CLIP response: detecting "broken swing"
    mock_response.json.return_value = [
        {"label": "broken swing", "score": 0.98},
        {"label": "safe playground", "score": 0.02}
    ]
    mock_http_client.post.return_value = mock_response

    img_bytes = create_test_image()

    with patch('backend.utils.validate_uploaded_file'):
        response = client.post(
            "/api/detect-playground-damage",
            files={"image": ("playground.jpg", img_bytes, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) == 1
    assert data["detections"][0]["label"] == "broken swing"

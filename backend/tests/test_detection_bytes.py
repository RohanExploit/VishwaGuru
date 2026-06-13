
import pytest
import warnings
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
import io
import json
from PIL import Image
import httpx
import sys
import os

# Suppress warnings for clean test output
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
from pathlib import Path

# Ensure repository root is importable so "backend" package resolves in tests
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set environment variable
os.environ['FRONTEND_URL'] = 'http://localhost:5173'

# Mock magic module before any imports
mock_magic = MagicMock()
mock_magic.from_buffer.return_value = "image/jpeg"
sys.modules['magic'] = mock_magic

# Mock telegram
mock_telegram = MagicMock()
sys.modules['telegram'] = mock_telegram
sys.modules['telegram.ext'] = mock_telegram.ext

# Mock dependencies before importing app
with patch("backend.main.create_all_ai_services") as mock_create_ai:
    mock_action = AsyncMock()
    mock_chat = AsyncMock()
    mock_summary = AsyncMock()
    mock_create_ai.return_value = (mock_action, mock_chat, mock_summary)

    from backend.main import app

@pytest.fixture
def client():
    # We want to mock httpx.AsyncClient but ensuring it returns a useful mock
    # The actual code calls:
    # client.post(API_URL, headers=headers, json=payload, timeout=20.0)

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"label": "graffiti", "score": 0.95}]
    mock_client.post.return_value = mock_response

    dummy_request = MagicMock()
    dummy_request.app.state.http_client = mock_client
    import backend.main as main_module
    main_module.request = dummy_request

    # We need to ensure that when main.py does app.state.http_client = httpx.AsyncClient()
    # it gets our mock, OR we set it after startup.

    # Let's rely on patching httpx.AsyncClient class constructor
    with patch("httpx.AsyncClient", return_value=mock_client):
         with TestClient(app) as c:
            yield c

@pytest.mark.asyncio
async def test_detect_vandalism_with_bytes(client):
    # We need to control the response for specific tests
    # Since client is fixture, the http_client is already initialized in app.state
    # We can access it via app.state.http_client (which is the mock_client from fixture)

    mock_client = app.state.http_client
    # Reset mock to ensure clean state
    mock_client.post.reset_mock()

    # Setup response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"label": "graffiti", "score": 0.95}]
    mock_client.post.return_value = mock_response

    # Create a dummy image bytes
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()

    # Send request
    with patch('backend.utils.validate_uploaded_file'), \
         patch('backend.pothole_detection.validate_image_for_processing'), \
         patch('backend.routers.detection.detect_vandalism_unified', AsyncMock(return_value=[{"label": "graffiti", "score": 0.95}])):
        response = client.post(
            "/api/detect-vandalism",
            files={"image": ("test.jpg", img_bytes, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) > 0
    assert data["detections"][0]["label"] == "graffiti"

    # Client not invoked because detection is mocked above

@pytest.mark.asyncio
async def test_detect_infrastructure_with_bytes(client):
    mock_client = app.state.http_client
    mock_client.post.reset_mock()

    # Setup response for infrastructure
    mock_response = MagicMock()
    mock_response.status_code = 200
    # damage_labels = ["broken streetlight", "damaged traffic sign", "fallen tree", "damaged fence"]
    mock_response.json.return_value = [{"label": "fallen tree", "score": 0.8}]
    mock_client.post.return_value = mock_response

    dummy_request = MagicMock()
    dummy_request.app.state.http_client = mock_client
    import backend.main as main_module
    main_module.request = dummy_request

    img = Image.new('RGB', (100, 100), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()

    with patch('backend.utils.validate_uploaded_file'), \
         patch('backend.pothole_detection.validate_image_for_processing'), \
         patch('backend.routers.detection.detect_infrastructure_unified', AsyncMock(return_value=[{"label": "fallen tree", "score": 0.8}])):
        response = client.post(
            "/api/detect-infrastructure",
            files={"image": ("test.jpg", img_bytes, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) > 0
    assert data["detections"][0]["label"] == "fallen tree"

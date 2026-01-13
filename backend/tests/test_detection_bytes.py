
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
import io
import json
from PIL import Image
import httpx

# Mock dependencies before importing app
with patch("backend.ai_factory.create_all_ai_services") as mock_create_ai:
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
    response = client.post(
        "/api/detect-vandalism",
        files={"image": ("test.jpg", img_bytes, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) > 0
    assert data["detections"][0]["label"] == "graffiti"

    # Verify client.post was called
    assert mock_client.post.called

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

    img = Image.new('RGB', (100, 100), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()

    response = client.post(
        "/api/detect-infrastructure",
        files={"image": ("test.jpg", img_bytes, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) > 0
    assert data["detections"][0]["label"] == "fallen tree"

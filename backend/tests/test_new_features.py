import pytest
import io
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from fastapi.testclient import TestClient

# Setup environment
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ['FRONTEND_URL'] = 'http://localhost:5173'

# Mock magic
mock_magic = MagicMock()
mock_magic.from_buffer.return_value = "image/jpeg"
sys.modules['magic'] = mock_magic

# Mock telegram
mock_telegram = MagicMock()
sys.modules['telegram'] = mock_telegram
sys.modules['telegram.ext'] = mock_telegram.ext

# Import main (will trigger app creation, but lifespan won't run yet)
import backend.main
from backend.main import app

@pytest.fixture
def client_with_mock_http():
    # Patch create_all_ai_services where it is used (in backend.main)
    with patch.object(backend.main, "create_all_ai_services") as mock_create:
         mock_create.return_value = (AsyncMock(), AsyncMock(), AsyncMock())

         # Mock http client
         mock_http = AsyncMock()
         # Option: Patch httpx.AsyncClient to return our mock
         mock_http.__aenter__.return_value = mock_http
         with patch("httpx.AsyncClient", return_value=mock_http):
             with TestClient(app) as c:
                 yield c, mock_http

def create_test_image():
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

def test_detect_waste(client_with_mock_http):
    client, mock_http = client_with_mock_http

    # Reset mock because startup might have called it?
    mock_http.post.reset_mock()

    # Mock HF API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"label": "plastic bottle", "score": 0.95}]
    mock_http.post.return_value = mock_response

    img_bytes = create_test_image()

    with patch('backend.utils.validate_uploaded_file'):
        response = client.post(
            "/api/detect-waste",
            files={"image": ("test.jpg", img_bytes, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["waste_type"] == "plastic bottle"
    assert data["confidence"] == 0.95

def test_detect_civic_eye(client_with_mock_http):
    client, mock_http = client_with_mock_http
    mock_http.post.reset_mock()

    # Mock HF API response (CLIP returns list of dicts)
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Provide results for all labels (safety, cleanliness, infra)
    mock_response.json.return_value = [
        {"label": "safe area", "score": 0.9},
        {"label": "clean street", "score": 0.85},
        {"label": "good infrastructure", "score": 0.8}
    ]
    mock_http.post.return_value = mock_response

    img_bytes = create_test_image()

    with patch('backend.utils.validate_uploaded_file'):
        response = client.post(
            "/api/detect-civic-eye",
            files={"image": ("test.jpg", img_bytes, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["safety"]["status"] == "safe area"
    assert data["cleanliness"]["status"] == "clean street"
    assert data["infrastructure"]["status"] == "good infrastructure"

def test_transcribe_audio(client_with_mock_http):
    client, mock_http = client_with_mock_http
    mock_http.post.reset_mock()

    # Mock Whisper response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"text": "This is a test transcription."}
    mock_http.post.return_value = mock_response

    audio_content = b"fake audio content"

    response = client.post(
        "/api/transcribe-audio",
        files={"file": ("test.wav", audio_content, "audio/wav")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "This is a test transcription."

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
from pathlib import Path

# Setup path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Mock environment variables
os.environ['FRONTEND_URL'] = 'http://localhost:5173'

# Mock heavy dependencies
sys.modules['ultralytics'] = MagicMock()
sys.modules['ultralyticsplus'] = MagicMock()

# Mock torch carefully for scipy/sklearn compatibility
mock_torch = MagicMock()
mock_torch.Tensor = type('Tensor', (), {})
sys.modules['torch'] = mock_torch

sys.modules['transformers'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['firebase_admin'] = MagicMock()

# Mock telegram package structure
mock_telegram = MagicMock()
sys.modules['telegram'] = mock_telegram
sys.modules['telegram.constants'] = MagicMock()
sys.modules['telegram.ext'] = MagicMock()
sys.modules['pywebpush'] = MagicMock()

# Mock dependencies for backend.main
# Pre-import backend.main to ensure it exists for patch
sys.modules["backend.ai_factory"] = MagicMock()
# sys.modules["backend.database"] = MagicMock()  # Don't mock database to avoid type hint issues with Base class
sys.modules["backend.init_db"] = MagicMock()
# Explicitly import modules so patch can find them
import backend.bot
import backend.init_db
import backend.ai_factory
import backend.routers.detection

# Now try importing backend.main inside patch context
with patch("backend.ai_factory.create_all_ai_services") as mock_create_ai:
    mock_create_ai.return_value = (AsyncMock(), AsyncMock(), AsyncMock())

    # We also need to mock migrate_db to prevent it from trying to connect to DB during import/startup
    with patch("backend.init_db.migrate_db"), patch("backend.bot.start_bot_thread"), patch("backend.bot.stop_bot_thread"):
        from backend.main import app

# Manually inject http_client into app state since TestClient might skip lifespan or we want a mock
app.state.http_client = AsyncMock()

client = TestClient(app)

def test_detect_traffic_sign_uses_process_uploaded_image():
    with patch("backend.routers.detection.process_uploaded_image", new_callable=AsyncMock) as mock_process:
        # Mock return value of process_uploaded_image (PIL Image, bytes)
        mock_process.return_value = (MagicMock(), b"processed_bytes")

        with patch("backend.routers.detection.detect_traffic_sign_clip", new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = [{"label": "damaged sign", "score": 0.9}]

            # Use a dummy file
            response = client.post(
                "/api/detect-traffic-sign",
                files={"image": ("test.jpg", b"raw_bytes", "image/jpeg")}
            )

            # Verify process_uploaded_image was called
            assert mock_process.call_count == 1
            # Verify detection was called with PROCESSED bytes, not raw bytes
            mock_detect.assert_called_once()
            args, _ = mock_detect.call_args
            assert args[0] == b"processed_bytes"

            assert response.status_code == 200
            assert response.json() == {"detections": [{"label": "damaged sign", "score": 0.9}]}

def test_detect_abandoned_vehicle_uses_process_uploaded_image():
    with patch("backend.routers.detection.process_uploaded_image", new_callable=AsyncMock) as mock_process:
        # Mock return value of process_uploaded_image (PIL Image, bytes)
        mock_process.return_value = (MagicMock(), b"processed_bytes_vehicle")

        with patch("backend.routers.detection.detect_abandoned_vehicle_clip", new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = [{"label": "abandoned car", "score": 0.85}]

            # Use a dummy file
            response = client.post(
                "/api/detect-abandoned-vehicle",
                files={"image": ("car.jpg", b"raw_bytes_vehicle", "image/jpeg")}
            )

            # Verify process_uploaded_image was called
            assert mock_process.call_count == 1
            # Verify detection was called with PROCESSED bytes
            mock_detect.assert_called_once()
            args, _ = mock_detect.call_args
            assert args[0] == b"processed_bytes_vehicle"

            assert response.status_code == 200
            assert response.json() == {"detections": [{"label": "abandoned car", "score": 0.85}]}

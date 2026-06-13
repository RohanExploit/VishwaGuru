import pytest
import warnings
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os
from pathlib import Path

# Suppress warnings for clean test output
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Ensure repository root is importable so "backend" package resolves in tests
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Also ensure backend directory is on path for direct module imports
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Set environment variable
os.environ['FRONTEND_URL'] = 'http://localhost:5173'

# Mock magic module
mock_magic = MagicMock()
mock_magic.from_buffer.return_value = "image/jpeg"
sys.modules['magic'] = mock_magic

# Mock telegram
mock_telegram = MagicMock()
sys.modules['telegram'] = mock_telegram
sys.modules['telegram.ext'] = mock_telegram.ext

from backend.main import app

@pytest.mark.asyncio
async def test_detect_severity_endpoint():
    # Mock AI services initialization to prevent startup failure
    with patch('backend.main.create_all_ai_services') as mock_create_services, \
         patch('backend.main.initialize_ai_services') as mock_init_services, \
         patch('backend.routers.detection.detect_severity_clip', new_callable=AsyncMock) as mock_detect:

        # Setup mocks
        mock_create_services.return_value = (MagicMock(), MagicMock(), MagicMock())

        # Define the mock return value for detection
        mock_detect.return_value = {
            "level": "Critical",
            "raw_label": "critical emergency",
            "confidence": 0.95
        }

        # Create a dummy image file
        file_content = b"fake image content"
        files = {"image": ("test.jpg", file_content, "image/jpeg")}

        # Use TestClient as context manager to trigger lifespan (startup/shutdown)
        with TestClient(app) as client:
            # Call the endpoint
            response = client.post("/api/detect-severity", files=files)

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["level"] == "Critical"
            assert data["raw_label"] == "critical emergency"
            assert data["confidence"] == 0.95

            # Verify the mock was called
            mock_detect.assert_called_once()

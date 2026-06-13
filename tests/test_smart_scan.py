from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.main import app
import pytest

def test_smart_scan_endpoint():
    with TestClient(app) as client:
        # Patch the function where it is imported in the ROUTER
        with patch("backend.routers.detection.detect_smart_scan_clip", new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = {"category": "pothole", "confidence": 0.95}

            file_content = b"fakeimagebytes"

            response = client.post(
                "/api/detect-smart-scan",
                files={"image": ("test.jpg", file_content, "image/jpeg")}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["category"] == "pothole"
            assert data["confidence"] == 0.95

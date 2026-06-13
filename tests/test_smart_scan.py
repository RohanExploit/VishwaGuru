from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.main import app
import pytest
from io import BytesIO
from PIL import Image

def test_smart_scan_endpoint():
    with TestClient(app) as client:
        # Patch the function where it is imported in the ROUTER
        with patch("backend.routers.detection._cached_detect_smart_scan", new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = {"category": "pothole", "confidence": 0.95}

            img = Image.new('RGB', (100, 100))
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG')
            file_content = img_bytes.getvalue()

            response = client.post(
                "/api/detect-smart-scan",
                files={"image": ("test.jpg", file_content, "image/jpeg")}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["category"] == "pothole"
            assert data["confidence"] == 0.95

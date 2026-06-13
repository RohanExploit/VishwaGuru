from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.main import app
import pytest
from io import BytesIO
from PIL import Image

@pytest.mark.asyncio
async def test_generate_description_endpoint():
    # Mock the generate_image_caption function in 'backend.routers.detection' module
    with patch("backend.routers.detection._cached_generate_caption", new_callable=AsyncMock) as mock_caption:
        mock_caption.return_value = "A photo of a pothole on the road"

        with TestClient(app) as client:
            # Create a dummy image
            img = Image.new('RGB', (100, 100))
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG')
            file_content = img_bytes.getvalue()

            files = {"image": ("test.jpg", file_content, "image/jpeg")}

            response = client.post("/api/generate-description", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["description"] == "A photo of a pothole on the road"

            # Verify the mock was called
            mock_caption.assert_called_once()

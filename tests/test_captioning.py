from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app
import pytest

@pytest.mark.asyncio
async def test_generate_description_endpoint():
    # Mock the generate_image_caption function in 'main' module
    with patch("main.generate_image_caption", new_callable=AsyncMock) as mock_caption:
        mock_caption.return_value = "A photo of a pothole on the road"

        with TestClient(app) as client:
            # Create a dummy image
            file_content = b"fake image content"
            files = {"image": ("test.jpg", file_content, "image/jpeg")}

            response = client.post("/api/generate-description", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["description"] == "A photo of a pothole on the road"

            # Verify the mock was called
            mock_caption.assert_called_once()

import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.hf_api_service import detect_smart_scan_clip
from PIL import Image
import io

@pytest.mark.asyncio
async def test_detect_smart_scan_clip_success():
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    mock_image_bytes = img_byte_arr.getvalue()

    mock_response_data = [
        {"label": "pothole", "score": 0.95},
        {"label": "garbage", "score": 0.03},
        {"label": "normal street", "score": 0.02}
    ]

    # Create a Mock Response object
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.text = "OK"

    # Mock httpx.AsyncClient
    mock_client = AsyncMock()
    # Ensure client.post is an AsyncMock that returns the mock_response when awaited
    mock_client.post.return_value = mock_response

    # Call the function
    result = await detect_smart_scan_clip(mock_image_bytes, client=mock_client)

    # Assertions
    assert result["category"] == "pothole"
    assert result["confidence"] == 0.95
    assert len(result["all_scores"]) == 3

@pytest.mark.asyncio
async def test_detect_smart_scan_clip_api_failure():
    mock_image = b"fake_image_bytes"

    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    result = await detect_smart_scan_clip(mock_image, client=mock_client)

    assert result["category"] == "unknown"
    assert result["confidence"] == 0

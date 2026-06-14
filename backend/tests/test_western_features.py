import sys
from unittest.mock import MagicMock, AsyncMock

# Mock heavy dependencies to avoid import errors
sys.modules["ultralytics"] = MagicMock()
sys.modules["ultralyticsplus"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["telegram"] = MagicMock()
sys.modules["telegram.ext"] = MagicMock()
sys.modules["telegram.error"] = MagicMock()
sys.modules["pywebpush"] = MagicMock()
sys.modules["firebase_admin"] = MagicMock()
sys.modules["sklearn"] = MagicMock()
sys.modules["scipy"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["cv2"] = MagicMock()

import pytest
from PIL import Image
from backend.hf_api_service import (
    detect_air_quality_clip,
    detect_playground_clip,
    detect_public_transport_clip,
    detect_cleanliness_clip
)

@pytest.mark.asyncio
async def test_detect_air_quality_clip():
    mock_client = AsyncMock()

    # Use MagicMock for response because .json() is synchronous
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"label": "smog", "score": 0.95},
        {"label": "clear sky", "score": 0.05}
    ]
    mock_client.post.return_value = mock_response

    img = Image.new('RGB', (100, 100), color='gray')
    result = await detect_air_quality_clip(img, client=mock_client)

    assert len(result) == 1
    assert result[0]['label'] == 'smog'
    assert result[0]['confidence'] == 0.95

@pytest.mark.asyncio
async def test_detect_playground_clip():
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"label": "broken swing", "score": 0.8},
        {"label": "safe playground", "score": 0.2}
    ]
    mock_client.post.return_value = mock_response

    img = Image.new('RGB', (100, 100), color='red')
    result = await detect_playground_clip(img, client=mock_client)

    assert len(result) == 1
    assert result[0]['label'] == 'broken swing'

@pytest.mark.asyncio
async def test_detect_public_transport_clip():
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"label": "damaged bus shelter", "score": 0.75},
        {"label": "clean bus stop", "score": 0.25}
    ]
    mock_client.post.return_value = mock_response

    img = Image.new('RGB', (100, 100), color='blue')
    result = await detect_public_transport_clip(img, client=mock_client)

    assert len(result) == 1
    assert result[0]['label'] == 'damaged bus shelter'

@pytest.mark.asyncio
async def test_detect_cleanliness_clip():
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"label": "overflowing garbage bin", "score": 0.88},
        {"label": "clean street", "score": 0.12}
    ]
    mock_client.post.return_value = mock_response

    img = Image.new('RGB', (100, 100), color='green')
    result = await detect_cleanliness_clip(img, client=mock_client)

    assert len(result) == 1
    assert result[0]['label'] == 'overflowing garbage bin'

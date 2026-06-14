import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.hf_api_service import analyze_urgency_text, detect_illegal_parking_clip
from PIL import Image
import io

@pytest.mark.asyncio
async def test_analyze_urgency_text_high():
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Mock response from Cardiff NLP model: list of list of dicts
    mock_response.json.return_value = [[
        {'label': 'negative', 'score': 0.95},
        {'label': 'neutral', 'score': 0.03},
        {'label': 'positive', 'score': 0.02}
    ]]
    mock_client.post.return_value = mock_response

    result = await analyze_urgency_text("This is a disaster! Very dangerous.", client=mock_client)

    assert result['urgency'] == 'High'
    assert result['sentiment'] == 'negative'
    assert result['score'] == 0.95

@pytest.mark.asyncio
async def test_analyze_urgency_text_medium():
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [[
        {'label': 'negative', 'score': 0.1},
        {'label': 'neutral', 'score': 0.8},
        {'label': 'positive', 'score': 0.1}
    ]]
    mock_client.post.return_value = mock_response

    result = await analyze_urgency_text("Just a normal observation.", client=mock_client)

    assert result['urgency'] == 'Medium'
    assert result['sentiment'] == 'neutral'

@pytest.mark.asyncio
async def test_detect_illegal_parking_clip():
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Mock response from CLIP model
    mock_response.json.return_value = [
        {'label': 'illegal parking', 'score': 0.9},
        {'label': 'empty street', 'score': 0.1}
    ]
    mock_client.post.return_value = mock_response

    # Create dummy image
    img = Image.new('RGB', (100, 100), color='red')

    result = await detect_illegal_parking_clip(img, client=mock_client)

    assert len(result) == 1
    assert result[0]['label'] == 'illegal parking'
    assert result[0]['confidence'] == 0.9

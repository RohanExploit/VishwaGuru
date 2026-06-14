import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from PIL import Image
import io
from backend.hf_api_service import detect_all_clip, detect_vandalism_clip, detect_infrastructure_clip, detect_flooding_clip

def create_test_image():
    img = Image.new('RGB', (100, 100), color='red')
    return img

@pytest.mark.asyncio
async def test_detect_all_clip():
    # Mock query_hf_api to return a list of results
    with patch("backend.hf_api_service.query_hf_api", new_callable=AsyncMock) as mock_query:
        # Simulate response from HF API for consolidated labels
        # Labels: vandalism, infrastructure, flooding, garbage, fire
        mock_query.return_value = [
            {"label": "graffiti", "score": 0.95}, # Vandalism target
            {"label": "pothole", "score": 0.8},  # Infrastructure target
            {"label": "normal road", "score": 0.05},
            {"label": "fire", "score": 0.1}
        ]

        image = create_test_image()
        results = await detect_all_clip(image)

        # Check structure
        assert "vandalism" in results
        assert "infrastructure" in results
        assert "flooding" in results
        assert "garbage" in results
        assert "fire" in results

        # Check specific detections
        vandalism = results["vandalism"]
        assert len(vandalism) == 1
        assert vandalism[0]["label"] == "graffiti"

        infrastructure = results["infrastructure"]
        assert len(infrastructure) == 1
        assert infrastructure[0]["label"] == "pothole"

        # Fire should be empty (score 0.1 < 0.4)
        assert len(results["fire"]) == 0

@pytest.mark.asyncio
async def test_detect_vandalism_clip():
    with patch("backend.hf_api_service.query_hf_api", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [
            {"label": "graffiti", "score": 0.9},
            {"label": "clean wall", "score": 0.1}
        ]

        image = create_test_image()
        results = await detect_vandalism_clip(image)

        assert len(results) == 1
        assert results[0]["label"] == "graffiti"

@pytest.mark.asyncio
async def test_detect_infrastructure_clip():
    with patch("backend.hf_api_service.query_hf_api", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [
            {"label": "broken streetlight", "score": 0.85}
        ]

        image = create_test_image()
        results = await detect_infrastructure_clip(image)

        assert len(results) == 1
        assert results[0]["label"] == "broken streetlight"

@pytest.mark.asyncio
async def test_detect_flooding_clip():
    with patch("backend.hf_api_service.query_hf_api", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [
            {"label": "flooded street", "score": 0.99}
        ]

        image = create_test_image()
        results = await detect_flooding_clip(image)

        assert len(results) == 1
        assert results[0]["label"] == "flooded street"

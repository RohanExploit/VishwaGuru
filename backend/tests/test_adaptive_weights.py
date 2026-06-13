import pytest
import os
import json
from unittest.mock import MagicMock, patch
from backend.adaptive_weights import AdaptiveWeights

@pytest.fixture
def clean_adaptive_weights(tmp_path):
    # Mock data directory to use a temp dir
    with patch("backend.adaptive_weights.os.path.dirname", return_value=str(tmp_path)):
        # Reset singleton instance
        AdaptiveWeights._instance = None

        # Ensure data/modelWeights.json exists or is clean
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        weights_file = data_dir / "modelWeights.json"

        # Instantiate
        aw = AdaptiveWeights()

        # Point to the temp file
        aw.weights_file = str(weights_file)
        aw.data_dir = str(data_dir)

        yield aw

        # Reset after test
        AdaptiveWeights._instance = None

def test_defaults(clean_adaptive_weights):
    aw = clean_adaptive_weights
    assert "critical" in aw.severity_keywords
    assert aw.duplicate_search_radius == 50.0

def test_save_and_load(clean_adaptive_weights):
    aw = clean_adaptive_weights
    # Use update method which calls save_weights
    aw.update_duplicate_radius(75.0)

    assert os.path.exists(aw.weights_file)

    # Reload manually to check content
    with open(aw.weights_file, 'r') as f:
        data = json.load(f)
        assert data["duplicate_search_radius"] == 75.0

def test_update_duplicate_radius(clean_adaptive_weights):
    aw = clean_adaptive_weights
    aw.update_duplicate_radius(60.0)
    assert aw.duplicate_search_radius == 60.0

    # Check if saved
    with open(aw.weights_file, 'r') as f:
        data = json.load(f)
        assert data["duplicate_search_radius"] == 60.0

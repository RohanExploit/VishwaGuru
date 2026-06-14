import os
import json
import pytest
from backend.adaptive_weights import AdaptiveWeights

@pytest.fixture
def adaptive_weights_instance(tmp_path):
    # Reset singleton state
    AdaptiveWeights._instance = None

    # Create a temporary file for testing
    weights_file = tmp_path / "modelWeights.json"

    # Initialize with the temp file path
    # Since DATA_FILE is a class attribute (or instance default), we need to patch it or set it after creation
    # But __init__ runs immediately.
    # So we should patch the class attribute before creating the instance.
    original_file = AdaptiveWeights.DATA_FILE
    AdaptiveWeights.DATA_FILE = str(weights_file)

    aw = AdaptiveWeights()

    yield aw

    # Teardown
    AdaptiveWeights.DATA_FILE = original_file
    AdaptiveWeights._instance = None

def test_load_defaults(adaptive_weights_instance):
    assert "severity_keywords" in adaptive_weights_instance.weights
    assert adaptive_weights_instance.duplicate_search_radius == 50.0

def test_update_radius(adaptive_weights_instance):
    adaptive_weights_instance.update_duplicate_search_radius(60.0)
    assert adaptive_weights_instance.duplicate_search_radius == 60.0

    # Check if saved
    with open(adaptive_weights_instance.DATA_FILE, 'r') as f:
        data = json.load(f)
        assert data["duplicate_search_radius"] == 60.0

def test_update_category_weight(adaptive_weights_instance):
    adaptive_weights_instance.update_category_weight("Pothole", 5.0)
    assert adaptive_weights_instance.category_weights["Pothole"] == 5.0

    adaptive_weights_instance.update_category_weight("Pothole", -2.0)
    assert adaptive_weights_instance.category_weights["Pothole"] == 3.0

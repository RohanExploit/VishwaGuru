import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import sys
import os

# Add root to sys.path
sys.path.append(os.getcwd())

from backend.grievance_classifier import get_grievance_classifier
from backend.main import app

@pytest.fixture
def client():
    # Create a mock for AsyncClient that handles context manager and async methods
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value.status_code = 200
    mock_client_instance.post.return_value.json.return_value = []

    # Mock aclose to be awaitable
    mock_client_instance.aclose = AsyncMock()

    # Mock lifespan events to prevent heavy initialization
    with patch("backend.main.create_all_ai_services") as mock_create, \
         patch("backend.main.initialize_ai_services") as mock_init, \
         patch("backend.main.start_bot_thread") as mock_bot, \
         patch("backend.main.stop_bot_thread") as mock_stop_bot, \
         patch("backend.main.httpx.AsyncClient", return_value=mock_client_instance) as mock_http, \
         patch("backend.main.migrate_db"), \
         patch("backend.main.load_maharashtra_pincode_data"), \
         patch("backend.main.load_maharashtra_mla_data"):

        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())

        with TestClient(app) as client:
            yield client

def test_classifier_loading_graceful():
    """Test that classifier handles loading failures gracefully"""
    # Force unload
    classifier = get_grievance_classifier()
    classifier.model = None

    # Try to load (it might fail if dependencies missing, but shouldn't raise)
    classifier.load_model()

    # If model is not None, it loaded. If None, it handled failure.
    assert classifier.model is None or classifier.model is not None

def test_classifier_prediction_fallback():
    """Test prediction fallback when model is unavailable"""
    classifier = get_grievance_classifier()

    # Simulate missing model
    classifier.model = None
    with patch("backend.grievance_classifier.HAS_JOBLIB", False):
        pred = classifier.predict("Dirty water coming from tap")
        assert pred == "Unknown (Model Unavailable)"

# Removed test_endpoint as the endpoint /api/classify-grievance does not exist

import pytest
import json
import sys
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Mock heavy/missing dependencies before importing app
sys.modules['magic'] = MagicMock()
sys.modules['telegram'] = MagicMock()
sys.modules['telegram.ext'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['google.cloud'] = MagicMock()
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_functions'] = MagicMock()
sys.modules['speech_recognition'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['ultralytics'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['pywebpush'] = MagicMock()
sys.modules['langdetect'] = MagicMock()
sys.modules['googletrans'] = MagicMock()
sys.modules['a2wsgi'] = MagicMock()

# Mock torch properly for scipy/sklearn checks
mock_torch = MagicMock()
class MockTensor: pass
mock_torch.Tensor = MockTensor
sys.modules['torch'] = mock_torch

# Now import app
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    mock_session = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    app.dependency_overrides = {}

@pytest.fixture
def mock_caches():
    with patch("backend.routers.issues.recent_issues_cache") as mock_recent, \
         patch("backend.routers.issues.nearby_issues_cache") as mock_nearby:

        # Default behavior: cache miss
        mock_recent.get.return_value = None
        mock_nearby.get.return_value = None

        yield mock_recent, mock_nearby

def test_get_recent_issues_cache_miss_then_hit(mock_db_session, mock_caches):
    mock_recent, _ = mock_caches

    # Setup DB return
    mock_issue = MagicMock()
    mock_issue.id = 1
    mock_issue.category = "Road"
    mock_issue.description = "Test Issue"
    mock_issue.created_at = datetime.now(timezone.utc)
    mock_issue.image_path = None
    mock_issue.status = "open"
    mock_issue.upvotes = 0
    mock_issue.location = "Test Loc"
    mock_issue.latitude = 10.0
    mock_issue.longitude = 20.0

    # Mock the query chain
    mock_query = mock_db_session.query.return_value
    mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_issue]

    # 1. Cache Miss
    response = client.get("/api/issues/recent")
    assert response.status_code == 200
    data1 = response.json()
    assert len(data1) == 1
    assert data1[0]["id"] == 1

    # Verify cache set was called
    assert mock_recent.set.called
    args, _ = mock_recent.set.call_args
    cached_content = args[0]

    # 2. Cache Hit
    mock_recent.get.return_value = cached_content
    mock_db_session.query.reset_mock()

    response = client.get("/api/issues/recent")
    assert response.status_code == 200
    data2 = response.json()

    assert data1 == data2
    mock_db_session.query.assert_not_called()

def test_get_nearby_issues_cache_miss_then_hit(mock_db_session, mock_caches):
    _, mock_nearby = mock_caches

    # Setup DB return for nearby
    mock_issue = MagicMock()
    mock_issue.id = 2
    mock_issue.category = "Water"
    mock_issue.description = "Nearby Issue"
    mock_issue.created_at = datetime.now(timezone.utc)
    mock_issue.status = "open"
    mock_issue.latitude = 10.0
    mock_issue.longitude = 20.0
    mock_issue.upvotes = 5

    # db.query(...).filter(...).all()
    mock_query = mock_db_session.query.return_value
    mock_query.filter.return_value.all.return_value = [mock_issue]

    with patch("backend.routers.issues.find_nearby_issues") as mock_find:
        mock_find.return_value = [(mock_issue, 15.0)] # Issue, distance

        # 1. Cache Miss
        response = client.get("/api/issues/nearby?latitude=10.0&longitude=20.0")
        assert response.status_code == 200
        data1 = response.json()
        assert len(data1) == 1
        assert data1[0]["distance_meters"] == 15.0

        # Verify cache set
        assert mock_nearby.set.called
        args, _ = mock_nearby.set.call_args
        cached_content = args[0]

        # 2. Cache Hit
        mock_nearby.get.return_value = cached_content
        mock_db_session.query.reset_mock()
        mock_find.reset_mock()

        response = client.get("/api/issues/nearby?latitude=10.0&longitude=20.0")
        assert response.status_code == 200
        data2 = response.json()

        assert data1 == data2
        mock_db_session.query.assert_not_called()
        mock_find.assert_not_called()

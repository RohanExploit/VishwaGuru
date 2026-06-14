import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from backend.main import app, get_db
from backend.models import Issue

# Create a mock database session
mock_db = MagicMock()

# Override the get_db dependency
def override_get_db():
    try:
        yield mock_db
    finally:
        pass

@pytest.fixture(scope="module", autouse=True)
def setup_overrides():
    app.dependency_overrides[get_db] = override_get_db
    # Mock http_client in app state
    app.state.http_client = MagicMock()
    yield
    app.dependency_overrides = {}

client = TestClient(app)

@patch("backend.main.validate_uploaded_file", new_callable=AsyncMock)
@patch("backend.main.verify_resolution_vqa", new_callable=AsyncMock)
def test_verify_issue_resolution_resolved(mock_verify, mock_validate):
    # Reset mock
    mock_db.reset_mock()

    # Setup mock DB return
    mock_issue = Issue(id=1, category="pothole", status="open", description="Big pothole")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_issue

    # Setup mock VQA response (Resolved -> "no" pothole visible)
    mock_verify.return_value = {"answer": "no", "confidence": 0.9}

    # Make request
    files = {"image": ("test.jpg", b"fake_image_bytes", "image/jpeg")}

    # Use patch context to handle validation bypass if needed, but we mocked validate_uploaded_file
    response = client.post("/api/issues/1/verify", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["is_resolved"] is True
    assert data["ai_answer"] == "no"

    # Verify DB commit was called
    mock_db.commit.assert_called()
    assert mock_issue.status == "verified"

@patch("backend.main.validate_uploaded_file", new_callable=AsyncMock)
@patch("backend.main.verify_resolution_vqa", new_callable=AsyncMock)
def test_verify_issue_resolution_not_resolved(mock_verify, mock_validate):
    # Reset mock
    mock_db.reset_mock()

    # Setup mock DB return
    mock_issue = Issue(id=1, category="pothole", status="open", description="Big pothole")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_issue

    # Setup mock VQA response (Not Resolved -> "yes" pothole visible)
    mock_verify.return_value = {"answer": "yes", "confidence": 0.9}

    # Make request
    files = {"image": ("test.jpg", b"fake_image_bytes", "image/jpeg")}

    response = client.post("/api/issues/1/verify", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["is_resolved"] is False

    # Verify DB commit was NOT called (or status didn't change)
    assert mock_issue.status == "open"

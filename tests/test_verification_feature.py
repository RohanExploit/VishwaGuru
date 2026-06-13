from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from backend.main import app
from backend.database import get_db

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

# Test Manual Verification (Upvote)
def test_manual_verification_upvote(client):
    # Mock DB dependency to return a fake issue
    mock_db = MagicMock()
    mock_issue = MagicMock()
    mock_issue.id = 1
    mock_issue.status = "open"
    mock_issue.upvotes = 2 # Initial upvotes

    # We need to mock the query chain: db.query().filter().first()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_issue

    # Mock Issue class for Issue.upvotes expression
    # Since we can't easily mock the expression evaluation in SQLAlchemy without a real DB or complex mocks,
    # we just verify the flow doesn't crash and calls commits/flush.
    # We patch run_in_threadpool to execute immediately or mock it.

    # Actually, we can rely on MagicMock accepting everything.

    # Override dependency
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        # We need to mock the query chain: db.query().filter().first() for updated_issue
        # The first call is for issue_data check, the second is for updated_issue check.
        mock_issue_data = MagicMock()
        mock_issue_data.id = 1
        mock_issue_data.category = "Road"
        mock_issue_data.status = "open"
        mock_issue_data.upvotes = 2

        mock_updated_issue = MagicMock()
        mock_updated_issue.upvotes = 5 # Reached threshold
        mock_updated_issue.status = "open"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_issue_data, # Initial check
            mock_updated_issue # After upvote increment
        ]

        # Mock update().filter().update()
        mock_db.query.return_value.filter.return_value.update.return_value = 1

        response = client.post("/api/issues/1/verify") # No image = manual

        assert response.status_code == 200
        # Check that update was called to set status to verified
        # We can verify that update was called with Issue.status: "verified"
        # Since we are using mocks, we check if update was called at least twice
        # (once for upvotes, once for status)
        assert mock_db.query.return_value.filter.return_value.update.call_count >= 2

        # Verify flush and commit were called
        assert mock_db.flush.called
        assert mock_db.commit.called

    finally:
        app.dependency_overrides = {}

# Test AI Verification
@patch("backend.routers.issues.validate_uploaded_file", new_callable=AsyncMock)
@patch("backend.routers.issues.verify_resolution_vqa", new_callable=AsyncMock)
def test_ai_verification_resolved(mock_vqa, mock_validate, client):
    # Setup mocks
    mock_validate.return_value = None
    mock_vqa.return_value = {
        "answer": "no",
        "confidence": 0.95
    }

    # Mock DB dependency to return a fake issue
    mock_db = MagicMock()
    mock_issue = MagicMock()
    mock_issue.id = 1
    mock_issue.category = "pothole"
    mock_issue.status = "open"
    mock_issue.upvotes = 0

    # We need to mock the query chain: db.query().filter().first()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_issue

    # Override dependency
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/issues/1/verify",
            files={"image": ("test.jpg", b"fakeimage", "image/jpeg")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_resolved"] == True
        assert data["ai_answer"] == "no"

    finally:
        app.dependency_overrides = {}

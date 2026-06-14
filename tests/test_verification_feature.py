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
        # Patch run_in_threadpool to just call the function
        # But verify_issue_endpoint calls `db.flush` which is a method on mock_db.
        # It calls `db.refresh(issue)`.

        # We need to simulate the upvote increment logic if possible,
        # but since it uses `Issue.upvotes + 2`, that expression will be a BinaryExpression object if Issue is real model.
        # Here mock_issue is a MagicMock. `mock_issue.upvotes` is 2 (int).
        # `Issue.upvotes` (class attribute) is an InstrumentedAttribute.
        # `issue.upvotes = Issue.upvotes + 2` -> This will assign a BinaryExpression to issue.upvotes.

        # This might fail if we try to read `issue.upvotes` later as an int.
        # In the endpoint: `if issue.upvotes >= 5`
        # If `issue.upvotes` is an expression, this comparison might fail or behave weirdly.

        # In a real SQLAlchemy session, `db.refresh(issue)` would update `issue.upvotes` to the integer value from DB.
        # With a Mock DB, `db.refresh(issue)` does nothing unless we make it do something.

        def mock_refresh(instance):
            # Simulate the DB update
            # We assume the expression was evaluated.
            # But since we can't easily evaluate the expression `Issue.upvotes + 2`,
            # we'll just manually set it for the test.
            instance.upvotes = 5 # Simulate it reached threshold

        mock_db.refresh.side_effect = mock_refresh

        # We need to patch the router logic slightly or rely on the side effect.
        # Since the code does: `issue.upvotes = Issue.upvotes + 2`
        # `Issue` is imported in `backend/routers/issues.py`.
        # `mock_issue` is what we got from query.

        # If we run this, `mock_issue.upvotes` becomes an expression.
        # Then `db.refresh(mock_issue)` is called. Our side_effect sets `mock_issue.upvotes = 5`.
        # Then `if mock_issue.upvotes >= 5` -> 5 >= 5 -> True.
        # Then `issue.status = "verified"`.
        # Then `db.commit()`.

        # This seems workable for a unit test of logic flow.

        response = client.post("/api/issues/1/verify") # No image = manual

        assert response.status_code == 200
        assert mock_issue.status == "verified"

        # Verify calls
        assert mock_db.flush.called
        assert mock_db.refresh.called
        assert mock_db.commit.called

    finally:
        app.dependency_overrides = {}

# Test AI Verification
@patch("backend.routers.issues.process_uploaded_image", new_callable=AsyncMock)
@patch("backend.routers.issues.verify_resolution_vqa", new_callable=AsyncMock)
def test_ai_verification_resolved(mock_vqa, mock_process, client):
    # Setup mocks
    from PIL import Image
    mock_process.return_value = (Image.new('RGB', (10, 10)), b"fakeimage")
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

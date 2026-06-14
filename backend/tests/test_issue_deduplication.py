import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import BackgroundTasks, UploadFile
from backend.routers.issues import create_issue
from backend.schemas import IssueCategory
from backend.models import Issue
from datetime import datetime

# Setup mock nearby issue
mock_nearby_issue = MagicMock()
mock_nearby_issue.id = 123
mock_nearby_issue.description = "Existing issue"
mock_nearby_issue.category = "Road"
mock_nearby_issue.status = "open"
mock_nearby_issue.created_at = datetime.now()
mock_nearby_issue.latitude = 10.0
mock_nearby_issue.longitude = 10.0
mock_nearby_issue.upvotes = 5

def mock_save_issue_db(db, issue):
    if issue.status == 'duplicate':
        issue.id = 999
    else:
        issue.id = 888
    return issue

@pytest.mark.asyncio
async def test_create_issue_duplicate():
    # Mock DB session
    mock_db = MagicMock()
    # Mock query chain for finding open issues
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.all.return_value = [mock_nearby_issue] # Return nearby issue

    # Mock request
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"

    # Mock background tasks
    mock_bg_tasks = MagicMock()

    with patch("backend.routers.issues.get_bounding_box", return_value=(0, 0, 0, 0)), \
         patch("backend.routers.issues.find_nearby_issues", return_value=[(mock_nearby_issue, 10.0)]), \
         patch("backend.routers.issues.check_upload_limits"), \
         patch("backend.routers.issues.save_issue_db", side_effect=mock_save_issue_db) as mock_save:

        # We don't patch run_in_threadpool, so it executes the lambdas which use our mock_db

        response = await create_issue(
            request=mock_request,
            background_tasks=mock_bg_tasks,
            description="Duplicate issue description",
            category=IssueCategory.ROAD.value,
            latitude=10.0,
            longitude=10.0,
            image=None,
            db=mock_db
        )

        # Check response
        assert response.deduplication_info.has_nearby_issues is True
        assert response.linked_issue_id == 123
        assert response.id is None # Expected behavior for duplicate

        # Verify save_issue_db was called with duplicate status
        args, _ = mock_save.call_args
        saved_issue = args[1] # 2nd arg is issue
        assert saved_issue.status == "duplicate"
        assert saved_issue.parent_issue_id == 123

@pytest.mark.asyncio
async def test_create_issue_new():
    # Mock DB session
    mock_db = MagicMock()

    mock_query_result = MagicMock()
    mock_filter_result = MagicMock()
    mock_order_result = MagicMock()

    mock_db.query.return_value = mock_query_result
    mock_query_result.filter.return_value = mock_filter_result
    # When filtering for open issues (1st call), return empty
    mock_filter_result.all.return_value = []

    # For prev_hash: query().order_by().first()
    mock_query_result.order_by.return_value = mock_order_result
    mock_order_result.first.return_value = ["prev_hash"] # prev hash

    # Mock request
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"

    # Mock background tasks
    mock_bg_tasks = MagicMock()

    with patch("backend.routers.issues.get_bounding_box", return_value=(0, 0, 0, 0)), \
         patch("backend.routers.issues.find_nearby_issues", return_value=[]), \
         patch("backend.routers.issues.check_upload_limits"), \
         patch("backend.routers.issues.save_issue_db", side_effect=mock_save_issue_db) as mock_save:

        response = await create_issue(
            request=mock_request,
            background_tasks=mock_bg_tasks,
            description="New issue description",
            category=IssueCategory.ROAD.value,
            latitude=10.0,
            longitude=10.0,
            image=None,
            db=mock_db
        )

        # Check response
        assert response.deduplication_info.has_nearby_issues is False
        assert response.id == 888
        assert response.linked_issue_id is None

        # Verify save_issue_db was called with open status
        args, _ = mock_save.call_args
        saved_issue = args[1]
        # status might be None (default) or "open" depending on init
        # For new issue, it's None in __init__ params in code
        assert saved_issue.status is None or saved_issue.status == "open"
        assert saved_issue.parent_issue_id is None

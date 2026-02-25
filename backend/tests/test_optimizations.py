import sys
from unittest.mock import MagicMock

# Create dummy classes for types used in isinstance/issubclass checks
class MockTensor: pass

mock_torch = MagicMock()
mock_torch.Tensor = MockTensor
sys.modules["torch"] = mock_torch

sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["ultralytics"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["telegram"] = MagicMock()
sys.modules["telegram.ext"] = MagicMock()
sys.modules["speech_recognition"] = MagicMock()
sys.modules["a2wsgi"] = MagicMock()
sys.modules["firebase_functions"] = MagicMock()
sys.modules["googletrans"] = MagicMock()
sys.modules["langdetect"] = MagicMock()

import pytest
from unittest.mock import MagicMock, patch
from fastapi.responses import JSONResponse
# We need to ensure we import these AFTER mocking
from backend.routers.issues import get_recent_issues, create_issue
from backend.cache import recent_issues_cache
import os
import shutil

# Test get_recent_issues return type
def test_get_recent_issues_return_type():
    # Mock cache
    mock_data = [{"id": 1, "description": "test"}]
    recent_issues_cache.set(mock_data, "recent_issues_10_0")

    # Mock DB
    db = MagicMock()

    # Call function
    response = get_recent_issues(limit=10, offset=0, db=db)

    # Check that response is NOT a JSONResponse, but the data itself
    assert not isinstance(response, JSONResponse)
    assert response == mock_data
    assert isinstance(response, list)

# Test create_issue cleanup
@pytest.mark.asyncio
async def test_create_issue_cleanup():
    # Mock dependencies
    request = MagicMock()
    background_tasks = MagicMock()
    db = MagicMock()

    # Mock file upload
    image = MagicMock()
    image.filename = "test.jpg"

    # Mock process_uploaded_image to return dummy data
    with patch("backend.routers.issues.process_uploaded_image") as mock_process:
        mock_process.return_value = (MagicMock(), b"fake_bytes")

        # Mock save_processed_image to create a dummy file
        with patch("backend.routers.issues.save_processed_image") as mock_save_image:
            def side_effect(bytes_data, path):
                # Create directory if needed
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    f.write(bytes_data)
            mock_save_image.side_effect = side_effect

            # Mock save_issue_db to raise exception
            with patch("backend.routers.issues.save_issue_db") as mock_save_db:
                mock_save_db.side_effect = Exception("DB Error")

                # Mock spatial utils
                with patch("backend.routers.issues.get_bounding_box") as mock_bbox:
                    mock_bbox.return_value = (0, 0, 0, 0)
                    with patch("backend.routers.issues.find_nearby_issues") as mock_nearby:
                        mock_nearby.return_value = []

                        # Mock rag_service
                        with patch("backend.routers.issues.rag_service") as mock_rag:
                             mock_rag.retrieve.return_value = None

                             # Call create_issue
                             try:
                                 await create_issue(
                                     request=request,
                                     background_tasks=background_tasks,
                                     description="Test description length check",
                                     category="Road",
                                     language="en",
                                     user_email="test@example.com",
                                     latitude=10.0,
                                     longitude=10.0,
                                     location="Test Loc",
                                     image=image,
                                     db=db
                                 )
                             except Exception as e:
                                 assert "Failed to save issue to database" in str(e)

                             # Check if file was cleaned up
                             args, _ = mock_save_image.call_args
                             file_path = args[1]

                             assert not os.path.exists(file_path), f"File {file_path} should have been deleted"

# Test get_recent_issues when not cached
def test_get_recent_issues_uncached():
    # Clear cache
    recent_issues_cache.clear()

    # Mock DB
    db = MagicMock()
    # Mock query result - create a Mock object that behaves like the row
    mock_row = MagicMock()
    mock_row.id = 1
    mock_row.description = "test"
    mock_row.category = "Road"
    mock_row.created_at = MagicMock()
    mock_row.created_at.isoformat.return_value = "2023-01-01"
    mock_row.image_path = "img.jpg"
    mock_row.status = "open"
    mock_row.upvotes = 0
    mock_row.location = "Loc"
    mock_row.latitude = 10.0
    mock_row.longitude = 10.0

    # Setup chain of calls: db.query(...).order_by(...).offset(...).limit(...).all()
    # Note: query() returns a Query object.
    mock_query = MagicMock()
    db.query.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = [mock_row]

    # Call function
    response = get_recent_issues(limit=10, offset=0, db=db)

    assert isinstance(response, list)
    assert len(response) == 1
    assert response[0]["id"] == 1

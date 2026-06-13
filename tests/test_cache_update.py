import os
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Set mock AI service to avoid external calls
os.environ["AI_SERVICE_TYPE"] = "mock"

from backend.main import app
from backend.cache import recent_issues_cache

client = TestClient(app)

def test_cache_invalidation_behavior():
    """
    Verifies the cache behavior during issue creation.
    """
    # Create a mock for the cache methods
    # We patch the object methods on the actual instance
    with patch.object(recent_issues_cache, 'clear') as mock_clear, \
         patch.object(recent_issues_cache, 'set') as mock_set, \
         patch.object(recent_issues_cache, 'get') as mock_get:

        # Setup initial cache state
        mock_get.return_value = [{"id": 999, "title": "Old Issue"}] # Simulate existing cache

        # Perform issue creation
        # We need to send a multipart request
        # Patch run_in_threadpool in the router where create_issue lives
        with patch('backend.routers.issues.run_in_threadpool') as mock_threadpool, \
             patch('backend.routers.issues.process_uploaded_image', new_callable=AsyncMock) as mock_process: # Patch validation

             mock_process.return_value = (MagicMock(), b"processed")

             # Mock the DB save to return a dummy issue with an ID
             mock_saved_issue = MagicMock()
             mock_saved_issue.id = 123
             mock_saved_issue.created_at = "2024-01-01T00:00:00"
             mock_saved_issue.description = "Test Description"
             mock_saved_issue.category = "Road"
             mock_saved_issue.status = "Reported"
             mock_saved_issue.upvotes = 0
             mock_saved_issue.image_path = "data/uploads/test.jpg"
             mock_saved_issue.location = None
             mock_saved_issue.latitude = None
             mock_saved_issue.longitude = None
             mock_saved_issue.action_plan = {"whatsapp": "msg"} # Dict, as expected by the optimization logic

             # We need to make sure run_in_threadpool returns this mock when called for save_issue_db
             # run_in_threadpool is called twice: file save, db save.
             def side_effect(func, *args, **kwargs):
                 # Check which function is being called
                 if getattr(func, '__name__', '') == 'save_issue_db':
                     # args[1] is new_issue (args[0] is db)
                     issue = args[1]
                     issue.id = 123
                     # Set fields that DB normally sets
                     import datetime
                     issue.created_at = datetime.datetime.now(datetime.timezone.utc)
                     issue.status = "Reported"
                     return issue
                 return None

             mock_threadpool.side_effect = side_effect

             response = client.post(
                "/api/issues",
                data={
                    "description": "Test Issue",
                    "category": "Road",
                },
                # Sending a small dummy image
                files={"image": ("test.jpg", b"fake image content", "image/jpeg")}
            )

        assert response.status_code == 201

        # NEW BEHAVIOR CHECK (After Pagination Update):
        # We now clear cache instead of optimistic update

        assert mock_clear.called, "Cache should be cleared"
        assert not mock_set.called, "Cache.set should NOT be called (optimistic update removed)"

        print("\n[Success] Cache behavior verified: Cleared cache for pagination consistency.")

if __name__ == "__main__":
    # verification via running with pytest
    pytest.main([__file__])

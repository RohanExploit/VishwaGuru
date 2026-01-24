import asyncio
import os
import shutil
import tempfile
from fastapi.testclient import TestClient

# Note: This test requires PYTHONPATH=. to be set to import backend modules
# Run with: PYTHONPATH=. python tests/test_issue_creation.py
import sys
import os

from backend.main import app
from backend.models import Base, Issue
from backend.database import engine, SessionLocal
import json

# Setup test DB
Base.metadata.create_all(bind=engine)

def test_create_issue():
    # Ensure mock AI services to avoid external calls
    os.environ["AI_SERVICE_TYPE"] = "mock"

    # Create a dummy image file (valid JPEG header)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        # Minimal JPEG header
        tmp.write(b'\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xff\xdb\x00\x43\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\x7f\xff\xd9')
        tmp_path = tmp.name

    try:
        from unittest.mock import patch, AsyncMock
        # Patch validation to avoid PIL/magic issues with dummy image
        with patch("backend.main.validate_uploaded_file", new_callable=AsyncMock) as mock_validate:
            with TestClient(app) as client:
                with open(tmp_path, "rb") as f:
                    response = client.post(
                        "/api/issues",
                        data={
                            "description": "Test Issue",
                            "category": "Road",
                            "user_email": "test@example.com"
                        },
                        files={"image": ("test.jpg", f, "image/jpeg")}
                    )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        assert response.status_code == 201
        assert "action_plan" in response.json()
        # Action plan should be None initially (async)
        assert response.json()["action_plan"] is None

        # Verify background task ran and updated DB
        # TestClient runs background tasks synchronously after request
        db = SessionLocal()
        issue = db.query(Issue).filter(Issue.id == response.json()["id"]).first()
        assert issue.action_plan is not None

        # Parse action plan
        # With JSONEncodedDict, issue.action_plan is already a dict
        plan = issue.action_plan
        assert plan.get("x_post")
        # Check if fallback or actual response
        # assert "@mybmc" in plan["x_post"]
        db.close()
    finally:
        os.remove(tmp_path)

if __name__ == "__main__":
    test_create_issue()

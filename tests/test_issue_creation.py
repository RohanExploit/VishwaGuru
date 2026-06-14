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
    # Create a valid minimal JPEG image file
    # This is the smallest valid JPEG file format
    jpeg_data = (
        b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xFF\xDB\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c'
        b'\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c'
        b'\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xFF\xC0\x00\x0b\x08\x00'
        b'\x01\x00\x01\x01\x01\x11\x00\xFF\xC4\x00\x14\x00\x01\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\t\xFF\xC4\x00\x14\x10\x01\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xDA\x00'
        b'\x08\x01\x01\x00\x00?\x00\x7f\xd9'
    )
    
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(jpeg_data)
        tmp_path = tmp.name

    try:
        from unittest.mock import patch, AsyncMock
        # Patch validation to avoid PIL/magic issues with dummy image
        # Also patch action plan generation to avoid external API calls
        # Note: Patch where it is imported/used (backend.main), not where it is defined
        with patch("backend.main.validate_uploaded_file", new_callable=AsyncMock) as mock_validate, \
             patch("backend.main.generate_action_plan", new_callable=AsyncMock) as mock_plan:

            mock_plan.return_value = {
                "whatsapp": "Test WhatsApp",
                "email_subject": "Test Subject",
                "email_body": "Test Body",
                "x_post": "Test X Post"
            }

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

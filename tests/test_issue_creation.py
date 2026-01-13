import asyncio
import os
import shutil
import tempfile
from fastapi.testclient import TestClient

# Note: This test requires PYTHONPATH=backend to be set to import backend modules
# Run with: PYTHONPATH=backend python tests/test_issue_creation.py
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app
from models import Base
from database import engine

# Setup test DB
Base.metadata.create_all(bind=engine)

def test_create_issue():
    # Ensure mock AI services to avoid external calls
    os.environ["AI_SERVICE_TYPE"] = "mock"

    # Create a dummy image file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(b"fake image content")
        tmp_path = tmp.name

    try:
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

        assert response.status_code == 200
        assert response.json()["message"] == "Issue reported successfully"
        assert "action_plan" in response.json()
        assert response.json()["action_plan"].get("x_post")
        assert "@mybmc" in response.json()["action_plan"]["x_post"]
    finally:
        os.remove(tmp_path)

if __name__ == "__main__":
    test_create_issue()

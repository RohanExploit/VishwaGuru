import asyncio
import os
import shutil
import tempfile
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import Base
from backend.database import engine

# Setup test DB
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_create_issue():
    # Create a dummy image file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(b"fake image content")
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            response = client.post(
                "/api/issues",
                data={
                    "description": "Test Issue",
                    "category": "Road"
                },
                files={"image": ("test.jpg", f, "image/jpeg")}
            )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        assert response.status_code == 200
        assert response.json()["message"] == "Issue reported successfully"
        assert "action_plan" in response.json()
    finally:
        os.remove(tmp_path)

if __name__ == "__main__":
    test_create_issue()

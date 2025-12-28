import os
import sys
import asyncio
from fastapi.testclient import TestClient

# Ensure backend is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app

client = TestClient(app)

def test_analyze_issue_endpoint():
    # Mocking HF_TOKEN env var is not enough because the service reads it at module level
    # But for the integration test, we expect the endpoint to return something even if token is missing
    # (The service catches exception and returns error or fallback)

    # Create a dummy image file (simulating bytes)
    fake_image_content = b"fake image bytes"

    # We are not mocking the external HF API call here, so this test relies on the service handling failures gracefully
    # or actually calling the API if credentials exist.
    # In this environment, HF_TOKEN is likely missing, so we expect a graceful failure or mock response.

    # However, to be safe and test the wiring, we can expect a 200 OK
    # even if the result says "Analysis Failed" or "Unknown".

    response = client.post(
        "/api/analyze-issue",
        files={"image": ("test.jpg", fake_image_content, "image/jpeg")}
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "label" in data
    assert "confidence" in data

    # If no token, it might return "Analysis Service Unavailable" or similar
    # But the endpoint works.

if __name__ == "__main__":
    test_analyze_issue_endpoint()

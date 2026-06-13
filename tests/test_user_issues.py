import sys
import os
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock environment variables
os.environ["FRONTEND_URL"] = "http://localhost:5173"
os.environ["GEMINI_API_KEY"] = "dummy"
os.environ["TELEGRAM_BOT_TOKEN"] = "dummy"

from backend.main import app

def test_get_user_issues_empty():
    with TestClient(app) as client:
        # Test with email that has no issues
        response = client.get("/api/issues/user?user_email=nonexistent@example.com")
        assert response.status_code == 200
        assert response.json() == []

if __name__ == "__main__":
    try:
        test_get_user_issues_empty()
        print("✅ test_get_user_issues_empty passed")
    except AssertionError as e:
        print(f"❌ test_get_user_issues_empty failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

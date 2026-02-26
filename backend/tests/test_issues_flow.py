import pytest
import sys
import os
import hashlib
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from fastapi.testclient import TestClient

# Setup environment
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Mock heavy dependencies before importing main
sys.modules['magic'] = MagicMock()
sys.modules['telegram'] = MagicMock()
sys.modules['telegram.ext'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['transformers'] = MagicMock()

# Mock torch correctly for issubclass checks in scipy/sklearn
class MockTensor:
    pass
mock_torch = MagicMock()
mock_torch.Tensor = MockTensor
sys.modules['torch'] = mock_torch

sys.modules['speech_recognition'] = MagicMock()
sys.modules['googletrans'] = MagicMock()
sys.modules['langdetect'] = MagicMock()
sys.modules['ultralytics'] = MagicMock()
sys.modules['a2wsgi'] = MagicMock()
sys.modules['firebase_functions'] = MagicMock()

# Mock pywebpush
mock_pywebpush = MagicMock()
mock_pywebpush.WebPushException = Exception
sys.modules['pywebpush'] = mock_pywebpush

import backend.main
from backend.main import app
from backend.models import Issue, Base
from backend.database import get_db, engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use file-based SQLite for testing to ensure thread safety with run_in_threadpool
TEST_DB_FILE = "test_issues.db"
if os.path.exists(TEST_DB_FILE):
    os.remove(TEST_DB_FILE)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Override dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    # Create tables
    Base.metadata.create_all(bind=test_engine)

    with patch("backend.main.create_all_ai_services") as mock_create:
        mock_create.return_value = (AsyncMock(), AsyncMock(), AsyncMock())
        # Also patch RAG service retrieve to avoid errors
        with patch("backend.routers.issues.rag_service.retrieve", return_value=None):
            with TestClient(app) as c:
                yield c

    # Cleanup
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

def test_create_issues_and_blockchain_chaining(client):
    # 1. Create first issue
    data1 = {
        "description": "First test issue for blockchain",
        "category": "Road",
        "latitude": 10.0,
        "longitude": 20.0
    }
    response1 = client.post("/api/issues", data=data1)
    assert response1.status_code == 201
    issue1_id = response1.json()["id"]

    # Verify issue 1 has integrity hash and empty previous hash (or logic handling it)
    with TestingSessionLocal() as db:
        issue1 = db.query(Issue).filter(Issue.id == issue1_id).first()
        assert issue1.integrity_hash is not None
        # First issue might have empty prev hash depending on DB state,
        # but here DB is fresh so it should be empty string or similar.
        expected_prev = ""
        expected_content = f"{data1['description']}|{data1['category']}|{expected_prev}"
        expected_hash = hashlib.sha256(expected_content.encode()).hexdigest()
        assert issue1.integrity_hash == expected_hash

        # Capture hash for next step
        prev_hash_for_2 = issue1.integrity_hash

    # 2. Create second issue
    data2 = {
        "description": "Second test issue for blockchain",
        "category": "Water",
        "latitude": 10.1, # Different enough to avoid dedupe
        "longitude": 20.1
    }
    response2 = client.post("/api/issues", data=data2)
    assert response2.status_code == 201
    issue2_id = response2.json()["id"]

    # Verify issue 2 links to issue 1
    with TestingSessionLocal() as db:
        issue2 = db.query(Issue).filter(Issue.id == issue2_id).first()
        assert issue2.previous_integrity_hash == prev_hash_for_2

        # Verify integrity hash computation
        expected_content_2 = f"{data2['description']}|{data2['category']}|{prev_hash_for_2}"
        expected_hash_2 = hashlib.sha256(expected_content_2.encode()).hexdigest()
        assert issue2.integrity_hash == expected_hash_2

    # 3. Call verification endpoint for Issue 2
    verify_response = client.get(f"/api/issues/{issue2_id}/blockchain-verify")
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert verify_data["is_valid"] is True
    assert verify_data["computed_hash"] == verify_data["current_hash"]
    assert "Integrity verified" in verify_data["message"]

def test_update_issue_status(client):
    # Create an issue first
    data = {
        "description": "Status update test issue",
        "category": "Garbage",
        "latitude": 11.0,
        "longitude": 21.0
    }
    create_res = client.post("/api/issues", data=data)
    issue_id = create_res.json()["id"]

    # Get reference_id
    with TestingSessionLocal() as db:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        ref_id = issue.reference_id
        initial_status = issue.status
        assert initial_status == "open"

    # Update status to verified
    update_data = {
        "reference_id": ref_id,
        "status": "verified",
        "notes": "Verified by test"
    }

    # Patch background tasks to avoid sending emails/notifications which might fail without creds
    with patch("backend.routers.issues.send_status_notification"):
        response = client.put("/api/issues/status", json=update_data)

    assert response.status_code == 200
    assert response.json()["status"] == "verified"

    # Verify DB update
    with TestingSessionLocal() as db:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        assert issue.status == "verified"
        assert issue.verified_at is not None

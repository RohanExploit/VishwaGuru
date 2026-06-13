
import sys
import os
sys.path.append(os.getcwd())
from unittest.mock import MagicMock

# Mock heavy dependencies BEFORE importing backend modules
sys.modules["ultralytics"] = MagicMock()
sys.modules["ultralyticsplus"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["telegram"] = MagicMock()
sys.modules["telegram.ext"] = MagicMock()
sys.modules["firebase_admin"] = MagicMock()
sys.modules["firebase_functions"] = MagicMock()
sys.modules["cv2"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
sys.modules["magic"] = MagicMock()
sys.modules["sklearn"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["scipy"] = MagicMock()
sys.modules["pywebpush"] = MagicMock()
sys.modules["async_lru"] = MagicMock()

from fastapi.testclient import TestClient
import pytest
import hashlib
from backend.main import app
from backend.database import get_db, Base, engine
from backend.models import Issue
from sqlalchemy.orm import Session

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}

def test_blockchain_verification_success(client, db_session):
    # Create first issue
    lat1, lon1 = 19.0760, 72.8777
    lat1_str, lon1_str = f"{lat1:.7f}", f"{lon1:.7f}"
    hash1_content = f"First issue|Road|{lat1_str}|{lon1_str}|"
    hash1 = hashlib.sha256(hash1_content.encode()).hexdigest()

    issue1 = Issue(
        description="First issue",
        category="Road",
        latitude=lat1,
        longitude=lon1,
        integrity_hash=hash1,
        previous_integrity_hash=""
    )
    db_session.add(issue1)
    db_session.commit()
    db_session.refresh(issue1)

    # Create second issue chained to first
    lat2, lon2 = 18.5204, 73.8567
    lat2_str, lon2_str = f"{lat2:.7f}", f"{lon2:.7f}"
    hash2_content = f"Second issue|Garbage|{lat2_str}|{lon2_str}|{hash1}"
    hash2 = hashlib.sha256(hash2_content.encode()).hexdigest()

    issue2 = Issue(
        description="Second issue",
        category="Garbage",
        latitude=lat2,
        longitude=lon2,
        integrity_hash=hash2,
        previous_integrity_hash=hash1
    )
    db_session.add(issue2)
    db_session.commit()
    db_session.refresh(issue2)

    # Verify first issue
    response = client.get(f"/api/issues/{issue1.id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == True
    assert data["current_hash"] == hash1

    # Verify second issue
    response = client.get(f"/api/issues/{issue2.id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == True
    assert data["current_hash"] == hash2

def test_blockchain_previous_hash_stored(client, db_session):
    # Create first issue
    hash1 = hashlib.sha256(b"First").hexdigest()
    issue1 = Issue(description="First", category="Road", integrity_hash=hash1)
    db_session.add(issue1)
    db_session.commit()

    # Create second issue via API (to test logic in create_issue)
    # Mocking background tasks to avoid errors
    from unittest.mock import patch
    with patch("backend.routers.issues.process_action_plan_background"), \
         patch("backend.routers.issues.create_grievance_from_issue_background"):
        response = client.post(
            "/api/issues",
            data={
                "description": "Second issue description",
                "category": "Garbage",
                "latitude": 10.0,
                "longitude": 20.0
            }
        )

    assert response.status_code == 201
    issue_id = response.json()["id"]

    # Verify issue in DB has previous_integrity_hash
    issue2 = db_session.query(Issue).filter(Issue.id == issue_id).first()
    assert issue2.previous_integrity_hash == hash1

    # Verify blockchain-verify endpoint uses the stored hash
    # (Implicitly tested if it returns is_valid=True and we know we didn't mock the internal DB query in the router)
    response = client.get(f"/api/issues/{issue_id}/blockchain-verify")
    assert response.status_code == 200
    assert response.json()["is_valid"] == True

def test_blockchain_verification_failure(client, db_session):
    # Create issue with tampered hash
    issue = Issue(
        description="Tampered issue",
        category="Road",
        latitude=19.0,
        longitude=72.0,
        integrity_hash="invalidhash",
        previous_integrity_hash="someprevhash"
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    response = client.get(f"/api/issues/{issue.id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == False
    assert data["message"].startswith("Integrity check failed")

def test_upvote_optimization(client, db_session):
    issue = Issue(
        description="Test issue for upvote",
        category="Road",
        upvotes=10
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    response = client.post(f"/api/issues/{issue.id}/vote")
    assert response.status_code == 200
    data = response.json()
    assert data["upvotes"] == 11

    # Verify in DB
    db_session.refresh(issue)
    assert issue.upvotes == 11

def test_blockchain_verification_legacy_fallback(client, db_session):
    # Test backward compatibility for issues without previous_integrity_hash

    # Create first issue
    hash1_content = "Legacy Issue 1|Road|"
    hash1 = hashlib.sha256(hash1_content.encode()).hexdigest()

    issue1 = Issue(
        description="Legacy Issue 1",
        category="Road",
        integrity_hash=hash1
        # previous_integrity_hash is None (default)
    )
    db_session.add(issue1)
    db_session.commit()
    db_session.refresh(issue1)

    # Create second issue chained to first
    hash2_content = f"Legacy Issue 2|Garbage|{hash1}"
    hash2 = hashlib.sha256(hash2_content.encode()).hexdigest()

    issue2 = Issue(
        description="Legacy Issue 2",
        category="Garbage",
        integrity_hash=hash2
        # previous_integrity_hash is None (default)
    )
    db_session.add(issue2)
    db_session.commit()
    db_session.refresh(issue2)

    # Verify second issue - should work via fallback query
    response = client.get(f"/api/issues/{issue2.id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == True
    assert data["current_hash"] == hash2

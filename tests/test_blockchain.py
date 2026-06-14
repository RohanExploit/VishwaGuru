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
    lat2, lon2 = 19.0761, 72.8778
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

def test_blockchain_backward_compatibility(client, db_session):
    # Create legacy issue (no previous_integrity_hash, old hash format)
    # Step 1: Create a predecessor
    prev_hash = "previoushash"
    issue_prev = Issue(
        description="Predecessor",
        category="Road",
        integrity_hash=prev_hash
    )
    db_session.add(issue_prev)
    db_session.commit()

    # Step 2: Create legacy issue chained to it
    legacy_content = f"Legacy issue|Road|{prev_hash}"
    legacy_hash = hashlib.sha256(legacy_content.encode()).hexdigest()

    issue_legacy = Issue(
        description="Legacy issue",
        category="Road",
        integrity_hash=legacy_hash,
        previous_integrity_hash=None # Explicitly None to simulate old records
    )
    db_session.add(issue_legacy)
    db_session.commit()
    db_session.refresh(issue_legacy)

    # Verify legacy issue - should use fallback logic
    response = client.get(f"/api/issues/{issue_legacy.id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == True
    assert data["current_hash"] == legacy_hash

def test_blockchain_verification_failure(client, db_session):
    # Create issue with tampered hash
    issue = Issue(
        description="Tampered issue",
        category="Road",
        integrity_hash="invalidhash"
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

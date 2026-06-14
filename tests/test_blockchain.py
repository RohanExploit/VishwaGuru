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
    hash1_content = "First issue|Road|"
    hash1 = hashlib.sha256(hash1_content.encode()).hexdigest()

    issue1 = Issue(
        description="First issue",
        category="Road",
        integrity_hash=hash1
    )
    db_session.add(issue1)
    db_session.commit()
    db_session.refresh(issue1)

    # Create second issue chained to first
    hash2_content = f"Second issue|Garbage|{hash1}"
    hash2 = hashlib.sha256(hash2_content.encode()).hexdigest()

    issue2 = Issue(
        description="Second issue",
        category="Garbage",
        integrity_hash=hash2
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

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

def test_blockchain_verification_legacy(client, db_session):
    """Test verification for legacy records (no previous_integrity_hash stored)"""
    # Create first issue
    hash1_content = "First issue|Road|"
    hash1 = hashlib.sha256(hash1_content.encode()).hexdigest()

    issue1 = Issue(
        description="First issue",
        category="Road",
        integrity_hash=hash1,
        previous_integrity_hash=None # Legacy record
    )
    db_session.add(issue1)
    db_session.commit()

    # Create second issue chained to first
    hash2_content = f"Second issue|Garbage|{hash1}"
    hash2 = hashlib.sha256(hash2_content.encode()).hexdigest()

    issue2 = Issue(
        description="Second issue",
        category="Garbage",
        integrity_hash=hash2,
        previous_integrity_hash=None # Legacy record
    )
    db_session.add(issue2)
    db_session.commit()

    # Verify first issue (O(log N) path)
    response = client.get(f"/api/issues/{issue1.id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == True
    assert data["current_hash"] == hash1

    # Verify second issue (O(log N) path)
    response = client.get(f"/api/issues/{issue2.id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == True
    assert data["current_hash"] == hash2

def test_blockchain_verification_optimized(client, db_session):
    """Test O(1) verification for new records (with previous_integrity_hash and lat/lon)"""
    lat, lon = 19.0760, 72.8777
    lat_str, lon_str = f"{lat:.7f}", f"{lon:.7f}"

    # Create first issue
    hash1_content = f"First issue|Road|{lat_str}|{lon_str}|"
    hash1 = hashlib.sha256(hash1_content.encode()).hexdigest()

    issue1 = Issue(
        description="First issue",
        category="Road",
        latitude=lat,
        longitude=lon,
        integrity_hash=hash1,
        previous_integrity_hash=""
    )
    db_session.add(issue1)
    db_session.commit()

    # Create second issue chained to first
    hash2_content = f"Second issue|Garbage|{lat_str}|{lon_str}|{hash1}"
    hash2 = hashlib.sha256(hash2_content.encode()).hexdigest()

    issue2 = Issue(
        description="Second issue",
        category="Garbage",
        latitude=lat,
        longitude=lon,
        integrity_hash=hash2,
        previous_integrity_hash=hash1
    )
    db_session.add(issue2)
    db_session.commit()

    # Verify second issue (O(1) path)
    response = client.get(f"/api/issues/{issue2.id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == True
    assert data["current_hash"] == hash2
    assert data["previous_hash"] == hash1

def test_blockchain_creation_and_verification_api(client, db_session):
    """End-to-end test: Create issues via API and verify their blockchain integrity"""
    # 1. Create first issue
    resp1 = client.post("/api/issues", data={
        "description": "API reported issue 1",
        "category": "Road",
        "latitude": 18.5204,
        "longitude": 73.8567
    })
    assert resp1.status_code == 201
    id1 = resp1.json()["id"]

    # 2. Verify first issue
    v_resp1 = client.get(f"/api/issues/{id1}/blockchain-verify")
    assert v_resp1.status_code == 200
    assert v_resp1.json()["is_valid"] == True
    hash1 = v_resp1.json()["current_hash"]

    # 3. Create second issue (should chain to first)
    # Use different location to avoid spatial deduplication
    resp2 = client.post("/api/issues", data={
        "description": "API reported issue 2",
        "category": "Garbage",
        "latitude": 19.0760,
        "longitude": 72.8777
    })
    assert resp2.status_code == 201
    id2 = resp2.json()["id"]

    # 4. Verify second issue
    v_resp2 = client.get(f"/api/issues/{id2}/blockchain-verify")
    assert v_resp2.status_code == 200
    assert v_resp2.json()["is_valid"] == True
    assert v_resp2.json()["previous_hash"] == hash1

def test_blockchain_verification_failure(client, db_session):
    # Create issue with tampered hash
    issue = Issue(
        description="Tampered issue",
        category="Road",
        integrity_hash="invalidhash",
        previous_integrity_hash=""
    )
    db_session.add(issue)
    db_session.commit()

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

    response = client.post(f"/api/issues/{issue.id}/vote")
    assert response.status_code == 200
    data = response.json()
    assert data["upvotes"] == 11

    # Verify in DB
    db_session.refresh(issue)
    assert issue.upvotes == 11

def test_blockchain_o1_optimization(client, db_session):
    # This test verifies that the previous_integrity_hash is stored
    # and used to avoid the extra query.

    # Create first issue
    response = client.post(
        "/api/issues",
        data={
            "description": "First issue for O1 test",
            "category": "Road"
        }
    )
    assert response.status_code == 201
    id1 = response.json()["id"]

    issue1 = db_session.query(Issue).filter(Issue.id == id1).first()
    hash1 = issue1.integrity_hash
    # The very first issue in an empty DB will have empty previous hash
    assert issue1.previous_integrity_hash == ""

    # Create second issue
    response = client.post(
        "/api/issues",
        data={
            "description": "Second issue for O1 test",
            "category": "Garbage"
        }
    )
    assert response.status_code == 201
    id2 = response.json()["id"]

    issue2 = db_session.query(Issue).filter(Issue.id == id2).first()
    # Check that it stored the hash of the first issue
    assert issue2.previous_integrity_hash == hash1

    # Verify the chain re-calculation logic matches
    expected_hash2_content = f"Second issue for O1 test|Garbage|{hash1}"
    expected_hash2 = hashlib.sha256(expected_hash2_content.encode()).hexdigest()
    assert issue2.integrity_hash == expected_hash2

    # Verify endpoint still works (it will use the O1 path internally)
    response = client.get(f"/api/issues/{id2}/blockchain-verify")
    assert response.status_code == 200
    assert response.json()["is_valid"] == True


import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.database import get_db, Base
from backend.models import FieldOfficerVisit, Issue
import hashlib
from datetime import datetime, timezone

# Setup test DB
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_blockchain.db"

@pytest.fixture
def test_db():
    engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_visit_blockchain_chaining(client, test_db):
    # 1. Create a dummy issue
    issue = Issue(
        description="Pothole in the road",
        category="Road",
        latitude=18.5204,
        longitude=73.8567,
        status="open"
    )
    test_db.add(issue)
    test_db.commit()
    test_db.refresh(issue)

    # 2. First check-in
    checkin_data1 = {
        "issue_id": issue.id,
        "officer_email": "officer1@example.com",
        "officer_name": "Officer One",
        "check_in_latitude": 18.5205,
        "check_in_longitude": 73.8568,
        "visit_notes": "First visit note"
    }
    response1 = client.post("/api/field-officer/check-in", json=checkin_data1)
    assert response1.status_code == 200
    data1 = response1.json()
    hash1 = data1["visit_hash"]
    # Adjust expectation to match Column behavior: empty string for first, but schema might return None if not set explicitly
    assert data1["previous_visit_hash"] in ["", None]

    # 3. Second check-in
    checkin_data2 = {
        "issue_id": issue.id,
        "officer_email": "officer2@example.com",
        "officer_name": "Officer Two",
        "check_in_latitude": 18.5206,
        "check_in_longitude": 73.8569,
        "visit_notes": "Second visit note"
    }
    response2 = client.post("/api/field-officer/check-in", json=checkin_data2)
    assert response2.status_code == 200
    data2 = response2.json()
    hash2 = data2["visit_hash"]
    assert data2["previous_visit_hash"] == hash1 # Should link to hash1

    # 4. Verify integrity of second visit
    verify_response = client.get(f"/api/field-officer/{data2['id']}/blockchain-verify")
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert verify_data["is_valid"] is True
    assert verify_data["current_hash"] == hash2

    # 5. Tamper with data and verify failure
    # We'll directly modify the DB for the second visit
    visit2 = test_db.query(FieldOfficerVisit).filter(FieldOfficerVisit.id == data2["id"]).first()
    visit2.visit_notes = "TAMPERED NOTES"
    test_db.commit()

    verify_response_tampered = client.get(f"/api/field-officer/{data2['id']}/blockchain-verify")
    assert verify_response_tampered.status_code == 200
    verify_data_tampered = verify_response_tampered.json()
    assert verify_data_tampered["is_valid"] is False
    assert verify_data_tampered["current_hash"] == hash2
    assert verify_data_tampered["computed_hash"] != hash2

def test_visit_blockchain_fallback_to_db(client, test_db):
    from backend.cache import visit_last_hash_cache

    # 1. Create dummy issue
    issue = Issue(
        description="Water leak",
        category="Water",
        latitude=18.5,
        longitude=73.8,
        status="open"
    )
    test_db.add(issue)
    test_db.commit()
    test_db.refresh(issue)

    # 2. First check-in
    client.post("/api/field-officer/check-in", json={
        "issue_id": issue.id,
        "officer_email": "o1@ex.com",
        "officer_name": "O1",
        "check_in_latitude": 18.5,
        "check_in_longitude": 73.8
    })

    # Clear cache to force DB lookup for next check-in
    visit_last_hash_cache.clear()

    # 3. Second check-in (should use DB lookup)
    response = client.post("/api/field-officer/check-in", json={
        "issue_id": issue.id,
        "officer_email": "o2@ex.com",
        "officer_name": "O2",
        "check_in_latitude": 18.5,
        "check_in_longitude": 73.8
    })
    assert response.status_code == 200
    data = response.json()
    assert data["previous_visit_hash"] not in ["", None]

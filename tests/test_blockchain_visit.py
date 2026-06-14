import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import hashlib

from backend.main import app
from backend.database import get_db, Base, engine
from backend.models import Issue, FieldOfficerVisit
from backend.cache import visit_last_hash_cache

# Use an isolated SQLite database for blockchain tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_blockchain_visit.db"

@pytest.fixture(scope="module")
def client():
    # Setup: Create tables in the test database
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    # Teardown: Remove the test database file if needed,
    # but here we just rely on the fact it's a separate file or in-memory
    Base.metadata.drop_all(bind=engine)

def test_visit_blockchain_chaining(client):
    # Clear cache for deterministic test
    visit_last_hash_cache.clear()

    # 1. Create a test issue
    db = next(get_db())
    issue = Issue(
        description="Pothole on Main St",
        category="Road",
        latitude=18.5204,
        longitude=73.8567,
        status="open"
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)

    # 2. First check-in (Root of the chain)
    checkin1 = {
        "issue_id": issue.id,
        "officer_email": "officer1@city.gov",
        "officer_name": "John Doe",
        "check_in_latitude": 18.5205,
        "check_in_longitude": 73.8568,
        "visit_notes": "First visit",
        "geofence_radius_meters": 100.0
    }
    response1 = client.post("/api/field-officer/check-in", json=checkin1)
    assert response1.status_code == 200
    data1 = response1.json()
    visit1_id = data1["id"]
    visit1_hash = data1.get("visit_hash") # Note: Visit hash is not in FieldOfficerVisitResponse by default in schemas.py?

    # Re-fetch from DB to check visit_hash and previous_visit_hash
    v1 = db.query(FieldOfficerVisit).filter(FieldOfficerVisit.id == visit1_id).first()
    assert v1.visit_hash is not None
    assert v1.previous_visit_hash == ""

    # 3. Second check-in (Chained to first)
    checkin2 = {
        "issue_id": issue.id,
        "officer_email": "officer2@city.gov",
        "officer_name": "Jane Smith",
        "check_in_latitude": 18.5204,
        "check_in_longitude": 73.8567,
        "visit_notes": "Second visit",
        "geofence_radius_meters": 100.0
    }
    response2 = client.post("/api/field-officer/check-in", json=checkin2)
    assert response2.status_code == 200
    data2 = response2.json()
    visit2_id = data2["id"]

    v2 = db.query(FieldOfficerVisit).filter(FieldOfficerVisit.id == visit2_id).first()
    assert v2.visit_hash is not None
    assert v2.previous_visit_hash == v1.visit_hash

    # 4. Verify integrity via API
    verify_resp1 = client.get(f"/api/field-officer/{visit1_id}/blockchain-verify")
    assert verify_resp1.status_code == 200
    assert verify_resp1.json()["is_valid"] is True

    verify_resp2 = client.get(f"/api/field-officer/{visit2_id}/blockchain-verify")
    assert verify_resp2.status_code == 200
    assert verify_resp2.json()["is_valid"] is True

    # 5. Simulate tampering
    v2.visit_notes = "TAMPERED NOTES"
    db.commit()

    verify_tampered = client.get(f"/api/field-officer/{visit2_id}/blockchain-verify")
    assert verify_tampered.status_code == 200
    assert verify_tampered.json()["is_valid"] is False
    assert "Integrity check failed" in verify_tampered.json()["message"]

def test_cache_miss_recovery(client):
    # 1. Create a visit
    db = next(get_db())
    issue = db.query(Issue).first()

    checkin = {
        "issue_id": issue.id,
        "officer_email": "officer3@city.gov",
        "officer_name": "Officer Cache",
        "check_in_latitude": 18.5204,
        "check_in_longitude": 73.8567,
        "visit_notes": "Cache test",
        "geofence_radius_meters": 100.0
    }
    client.post("/api/field-officer/check-in", json=checkin)

    last_visit = db.query(FieldOfficerVisit).order_by(FieldOfficerVisit.id.desc()).first()
    last_hash = last_visit.visit_hash

    # 2. Clear cache
    visit_last_hash_cache.clear()

    # 3. Next check-in should still chain correctly by fetching from DB
    checkin_next = {
        "issue_id": issue.id,
        "officer_email": "officer4@city.gov",
        "officer_name": "Officer Recovery",
        "check_in_latitude": 18.5204,
        "check_in_longitude": 73.8567,
        "visit_notes": "Recovery test",
        "geofence_radius_meters": 100.0
    }
    resp = client.post("/api/field-officer/check-in", json=checkin_next)
    assert resp.status_code == 200

    v_next = db.query(FieldOfficerVisit).order_by(FieldOfficerVisit.id.desc()).first()
    assert v_next.previous_visit_hash == last_hash

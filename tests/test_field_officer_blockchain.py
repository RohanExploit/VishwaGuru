import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.main import app
from backend.database import get_db, Base, engine
from backend.models import FieldOfficerVisit, Issue
from datetime import datetime, timezone
import uuid

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)

    # Create a dummy issue for testing
    issue = Issue(
        reference_id=str(uuid.uuid4()),
        description="Test issue for field officer visit",
        category="Road",
        status="open",
        latitude=19.0760,
        longitude=72.8777
    )
    session.add(issue)
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}

def test_field_officer_visit_blockchain_chaining(client, db_session):
    # Get the issue ID
    issue = db_session.query(Issue).first()
    issue_id = issue.id

    # Create first visit
    check_in_data1 = {
        "issue_id": issue_id,
        "officer_email": "officer1@example.com",
        "officer_name": "Officer One",
        "check_in_latitude": 19.0761,
        "check_in_longitude": 72.8778,
        "visit_notes": "First visit check-in"
    }

    response = client.post("/api/field-officer/check-in", json=check_in_data1)
    assert response.status_code == 200
    visit1_data = response.json()
    visit1_id = visit1_data["id"]
    visit1_hash = visit1_data["visit_hash"]

    # Verify first visit integrity
    response = client.get(f"/api/field-officer/visit/{visit1_id}/blockchain-verify")
    assert response.status_code == 200
    verify_data = response.json()
    assert verify_data["is_valid"] is True
    assert verify_data["current_hash"] == visit1_hash

    # Create second visit - should be chained to the first one
    check_in_data2 = {
        "issue_id": issue_id,
        "officer_email": "officer2@example.com",
        "officer_name": "Officer Two",
        "check_in_latitude": 19.0762,
        "check_in_longitude": 72.8779,
        "visit_notes": "Second visit check-in"
    }

    response = client.post("/api/field-officer/check-in", json=check_in_data2)
    assert response.status_code == 200
    visit2_data = response.json()
    visit2_id = visit2_data["id"]
    visit2_hash = visit2_data["visit_hash"]

    # Check chaining
    visit2_db = db_session.query(FieldOfficerVisit).filter(FieldOfficerVisit.id == visit2_id).first()
    assert visit2_db.previous_visit_hash == visit1_hash

    # Verify second visit integrity
    response = client.get(f"/api/field-officer/visit/{visit2_id}/blockchain-verify")
    assert response.status_code == 200
    verify_data = response.json()
    assert verify_data["is_valid"] is True
    assert verify_data["current_hash"] == visit2_hash

def test_field_officer_visit_blockchain_tamper_detection(client, db_session):
    # Get the issue ID
    issue = db_session.query(Issue).first()
    issue_id = issue.id

    # Create a visit
    check_in_data = {
        "issue_id": issue_id,
        "officer_email": "officer@example.com",
        "officer_name": "Officer One",
        "check_in_latitude": 19.0761,
        "check_in_longitude": 72.8778,
        "visit_notes": "Original notes"
    }

    response = client.post("/api/field-officer/check-in", json=check_in_data)
    visit_id = response.json()["id"]

    # Verify initially valid
    response = client.get(f"/api/field-officer/visit/{visit_id}/blockchain-verify")
    assert response.json()["is_valid"] is True

    # Tamper with the data (e.g., change notes in DB)
    db_session.query(FieldOfficerVisit).filter(FieldOfficerVisit.id == visit_id).update({"visit_notes": "Tampered notes"})
    db_session.commit()

    # Verification should now fail
    response = client.get(f"/api/field-officer/visit/{visit_id}/blockchain-verify")
    assert response.status_code == 200
    verify_data = response.json()
    assert verify_data["is_valid"] is False
    assert "Integrity check failed" in verify_data["message"]

def test_field_officer_visit_blockchain_chain_tamper_detection(client, db_session):
    # Get the issue ID
    issue = db_session.query(Issue).first()
    issue_id = issue.id

    # Create visit 1
    client.post("/api/field-officer/check-in", json={
        "issue_id": issue_id,
        "officer_email": "officer1@example.com",
        "officer_name": "Officer One",
        "check_in_latitude": 19.0761,
        "check_in_longitude": 72.8778
    })

    # Create visit 2
    response = client.post("/api/field-officer/check-in", json={
        "issue_id": issue_id,
        "officer_email": "officer2@example.com",
        "officer_name": "Officer Two",
        "check_in_latitude": 19.0762,
        "check_in_longitude": 72.8779
    })
    visit2_id = response.json()["id"]

    # Verify initially valid
    response = client.get(f"/api/field-officer/visit/{visit2_id}/blockchain-verify")
    assert response.json()["is_valid"] is True

    # Tamper with the chain: change previous_visit_hash of visit 2
    db_session.query(FieldOfficerVisit).filter(FieldOfficerVisit.id == visit2_id).update({"previous_visit_hash": "corrupted_chain_link"})
    db_session.commit()

    # Verification should fail because recomputed hash (with wrong prev_hash) won't match stored hash
    response = client.get(f"/api/field-officer/visit/{visit2_id}/blockchain-verify")
    assert response.json()["is_valid"] is False

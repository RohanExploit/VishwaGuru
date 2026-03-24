import pytest
import hashlib
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.main import app
from backend.database import get_db, Base, engine
from backend.models import Grievance, Jurisdiction, JurisdictionLevel, SeverityLevel
from backend.grievance_service import GrievanceService
from datetime import datetime, timezone, timedelta

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)

    # Create a dummy jurisdiction for testing
    jurisdiction = Jurisdiction(
        level=JurisdictionLevel.DISTRICT,
        geographic_coverage={"cities": ["Mumbai"], "districts": ["Mumbai"], "states": ["Maharashtra"]},
        responsible_authority="Mumbai Municipal Corporation",
        default_sla_hours=24
    )
    session.add(jurisdiction)
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

def test_grievance_blockchain_integrity(client, db_session):
    service = GrievanceService()

    # Create first grievance
    grievance_data1 = {
        "category": "health",
        "severity": "high",
        "city": "Mumbai",
        "district": "Mumbai",
        "state": "Maharashtra",
        "description": "First grievance"
    }

    g1 = service.create_grievance(grievance_data1, db=db_session)
    assert g1 is not None
    assert g1.integrity_hash is not None
    assert g1.previous_integrity_hash == ""

    # Verify via API
    response = client.get(f"/api/grievances/{g1.id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["current_hash"] == g1.integrity_hash

    # Create second grievance chained to first
    grievance_data2 = {
        "category": "police",
        "severity": "medium",
        "city": "Mumbai",
        "district": "Mumbai",
        "state": "Maharashtra",
        "description": "Second grievance"
    }

    g2 = service.create_grievance(grievance_data2, db=db_session)
    assert g2 is not None
    assert g2.previous_integrity_hash == g1.integrity_hash

    # Verify second grievance via API
    response = client.get(f"/api/grievances/{g2.id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["current_hash"] == g2.integrity_hash

def test_grievance_blockchain_failure(client, db_session):
    service = GrievanceService()

    grievance_data = {
        "category": "health",
        "severity": "high",
        "city": "Mumbai",
        "description": "Tamper test"
    }

    g = service.create_grievance(grievance_data, db=db_session)

    # Manually tamper with the hash in DB
    db_session.query(Grievance).filter(Grievance.id == g.id).update({"integrity_hash": "tampered_hash"})
    db_session.commit()

    # Verify via API should fail
    response = client.get(f"/api/grievances/{g.id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert "Integrity check failed" in data["message"]

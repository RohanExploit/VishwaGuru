from fastapi.testclient import TestClient
import pytest
import hashlib
from backend.main import app
from backend.database import get_db, Base, engine
from backend.models import Grievance, Jurisdiction, JurisdictionLevel, SeverityLevel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    # Create a jurisdiction which is required for grievance
    jurisdiction = Jurisdiction(
        level=JurisdictionLevel.LOCAL,
        geographic_coverage={"cities": ["Mumbai"]},
        responsible_authority="Mumbai MC",
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

def test_grievance_blockchain_chaining(client, db_session):
    # Create two grievances through the API/Service logic would be better but let's test the chaining manually first then through service
    from backend.grievance_service import GrievanceService
    service = GrievanceService()

    # Reset cache to ensure clean state
    from backend.cache import grievance_last_hash_cache
    grievance_last_hash_cache.clear()

    # Grievance 1
    g1_data = {
        "category": "Road",
        "severity": "medium",
        "city": "Mumbai",
        "description": "Pothole in sector 5"
    }
    g1 = service.create_grievance(g1_data, db=db_session)
    assert g1 is not None
    assert g1.integrity_hash is not None
    assert g1.previous_integrity_hash == ""

    # Grievance 2
    g2_data = {
        "category": "Garbage",
        "severity": "high",
        "city": "Mumbai",
        "description": "Waste overflow"
    }
    g2 = service.create_grievance(g2_data, db=db_session)
    assert g2 is not None
    assert g2.integrity_hash is not None
    assert g2.previous_integrity_hash == g1.integrity_hash

    # Verify through API
    response = client.get(f"/grievances/{g1.id}/blockchain-verify")
    assert response.status_code == 200
    assert response.json()["is_valid"] == True

    response = client.get(f"/grievances/{g2.id}/blockchain-verify")
    assert response.status_code == 200
    assert response.json()["is_valid"] == True

def test_grievance_blockchain_failure(client, db_session):
    # Manually create a tampered grievance
    jurisdiction = db_session.query(Jurisdiction).first()
    g = Grievance(
        unique_id="TAMPERED",
        category="Road",
        severity=SeverityLevel.MEDIUM,
        current_jurisdiction_id=jurisdiction.id,
        assigned_authority="Mumbai MC",
        sla_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
        integrity_hash="fakehash",
        previous_integrity_hash=""
    )
    db_session.add(g)
    db_session.commit()

    response = client.get(f"/grievances/{g.id}/blockchain-verify")
    assert response.status_code == 200
    assert response.json()["is_valid"] == False
    assert "Integrity check failed" in response.json()["message"]

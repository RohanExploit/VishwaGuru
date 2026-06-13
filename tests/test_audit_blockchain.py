from fastapi.testclient import TestClient
import pytest
import hashlib
import hmac
import os
import json
from backend.main import app
from backend.database import get_db, Base, engine
from backend.models import Issue, Grievance, Jurisdiction, EscalationAudit, EscalationReason, SeverityLevel, JurisdictionLevel, GrievanceStatus
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)

    # Setup initial jurisdiction (LOCAL)
    jurisdiction = Jurisdiction(
        level=JurisdictionLevel.LOCAL,
        geographic_coverage={"states": ["Maharashtra"]},
        responsible_authority="Local Authority",
        default_sla_hours=24
    )
    session.add(jurisdiction)

    # Setup DISTRICT jurisdiction for escalation
    district_jurisdiction = Jurisdiction(
        level=JurisdictionLevel.DISTRICT,
        geographic_coverage={"states": ["Maharashtra"]},
        responsible_authority="District Authority",
        default_sla_hours=48
    )
    session.add(district_jurisdiction)

    # Setup STATE jurisdiction for second escalation
    state_jurisdiction = Jurisdiction(
        level=JurisdictionLevel.STATE,
        geographic_coverage={"states": ["Maharashtra"]},
        responsible_authority="State Authority",
        default_sla_hours=72
    )
    session.add(state_jurisdiction)

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

def test_audit_blockchain_chaining(client, db_session):
    # Setup Grievance with state=Maharashtra to match seeded jurisdictions
    # Use health category to match "District Health Department" in rules
    grievance = Grievance(
        unique_id="G123",
        category="health",
        severity=SeverityLevel.MEDIUM,
        state="Maharashtra",
        current_jurisdiction_id=1,
        assigned_authority="Local Authority",
        sla_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
        status=GrievanceStatus.OPEN
    )
    db_session.add(grievance)
    db_session.commit()
    grievance_id = grievance.id

    # Create first manual escalation (Audit 1)
    secret_key = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7").encode()

    from backend.grievance_service import GrievanceService
    service = GrievanceService()

    # Manual escalation logic:
    # 1. Finds next level (LOCAL -> DISTRICT)
    # 2. Finds jurisdiction for DISTRICT in Maharashtra
    # 3. Assigns authority for 'health' in that jurisdiction
    # In rules: 'health' has authority: "District Health Department"

    success = service.escalation_engine.manual_escalate(grievance_id, reason="Test Escalation 1", db=db_session)
    assert success == True

    audit1 = db_session.query(EscalationAudit).filter(EscalationAudit.id == 1).first()
    assert audit1 is not None
    assert audit1.previous_integrity_hash == ""

    # Expected: Local Authority -> District Health Department
    expected_hash1_content = f"{grievance_id}|Local Authority|District Health Department|manual|"
    expected_hash1 = hmac.new(secret_key, expected_hash1_content.encode(), hashlib.sha256).hexdigest()
    assert audit1.integrity_hash == expected_hash1

    # Create second manual escalation (Audit 2)
    # DISTRICT -> STATE
    # In rules: 'health' has authority override "District Health Department" globally in categories.
    # Wait, categories.health.authority = "District Health Department"
    # So it will stay "District Health Department" even at State level?
    # Let's check rules.json again.
    # "health": { "jurisdiction_level": "district", "authority": "District Health Department" }
    # RoutingService.assign_authority uses category_rules.get('authority') if it exists.
    # So it will stay "District Health Department".

    success = service.escalation_engine.manual_escalate(grievance_id, reason="Test Escalation 2", db=db_session)
    assert success == True

    audit2 = db_session.query(EscalationAudit).filter(EscalationAudit.id == 2).first()
    assert audit2 is not None
    assert audit2.previous_integrity_hash == expected_hash1

    # District Health Department -> District Health Department
    expected_hash2_content = f"{grievance_id}|District Health Department|District Health Department|manual|{expected_hash1}"
    expected_hash2 = hmac.new(secret_key, expected_hash2_content.encode(), hashlib.sha256).hexdigest()
    assert audit2.integrity_hash == expected_hash2

    # Verify via API
    response = client.get(f"/api/grievances/audit/{audit2.id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == True
    assert data["current_hash"] == expected_hash2
    assert "Integrity verified" in data["message"]

def test_audit_blockchain_tamper_detection(client, db_session):
    # Setup Grievance and one Audit
    grievance = Grievance(
        unique_id="G456",
        category="health",
        severity=SeverityLevel.HIGH,
        state="Maharashtra",
        current_jurisdiction_id=1,
        assigned_authority="Local Authority",
        sla_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
        status=GrievanceStatus.OPEN
    )
    db_session.add(grievance)
    db_session.commit()
    grievance_id = grievance.id

    from backend.grievance_service import GrievanceService
    service = GrievanceService()
    service.escalation_engine.manual_escalate(grievance_id, reason="Tamper Test", db=db_session)

    audit = db_session.query(EscalationAudit).first()
    assert audit is not None
    audit_id = audit.id
    original_hash = audit.integrity_hash

    # Tamper with the data
    audit.new_authority = "Fake Authority"
    db_session.commit()

    # Verify via API
    response = client.get(f"/api/grievances/audit/{audit_id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == False
    assert data["current_hash"] == original_hash
    assert data["computed_hash"] != original_hash
    assert "Integrity check failed" in data["message"]

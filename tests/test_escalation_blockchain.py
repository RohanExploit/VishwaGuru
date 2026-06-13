import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base, get_db
from backend.main import app
from backend.models import Grievance, EscalationAudit, Jurisdiction, JurisdictionLevel, SeverityLevel, EscalationReason
from backend.cache import audit_last_hash_cache
import hashlib

# Use an isolated SQLite database for blockchain tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_escalation_blockchain.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_escalation_audit_blockchain_chaining(client, db_session):
    # Setup: Clear cache and create jurisdictions
    audit_last_hash_cache.clear()

    j1 = Jurisdiction(level=JurisdictionLevel.LOCAL, geographic_coverage={"cities": ["Mumbai"]}, responsible_authority="Ward Officer", default_sla_hours=24)
    j2 = Jurisdiction(level=JurisdictionLevel.DISTRICT, geographic_coverage={"districts": ["Mumbai"]}, responsible_authority="District Collector", default_sla_hours=48)
    db_session.add_all([j1, j2])
    db_session.commit()

    # Create a grievance
    g = Grievance(
        unique_id="G123",
        category="Road",
        severity=SeverityLevel.MEDIUM,
        current_jurisdiction_id=j1.id,
        assigned_authority="Ward Officer",
        sla_deadline=pytest.importorskip("datetime").datetime.now()
    )
    db_session.add(g)
    db_session.commit()

    # Trigger escalation (manually to test logic)
    from backend.escalation_engine import EscalationEngine
    from backend.routing_service import RoutingService
    from backend.sla_config_service import SLAConfigService

    routing = RoutingService({})
    sla = SLAConfigService()
    engine_ext = EscalationEngine(routing, sla, {})

    # Mock routing for escalation
    routing._find_jurisdiction = lambda **kwargs: j2
    routing.assign_authority = lambda j, c: j.responsible_authority
    routing.get_next_jurisdiction_level = lambda l: JurisdictionLevel.DISTRICT

    # First Escalation
    engine_ext._escalate_grievance(g, EscalationReason.MANUAL, db_session, "First escalation")

    audit1 = db_session.query(EscalationAudit).filter(EscalationAudit.grievance_id == g.id).first()
    assert audit1 is not None
    assert audit1.integrity_hash is not None
    assert audit1.previous_integrity_hash == ""

    # Second Escalation (to test chaining)
    j3 = Jurisdiction(level=JurisdictionLevel.STATE, geographic_coverage={"states": ["Maharashtra"]}, responsible_authority="State Secretary", default_sla_hours=72)
    db_session.add(j3)
    db_session.commit()

    routing._find_jurisdiction = lambda **kwargs: j3
    routing.get_next_jurisdiction_level = lambda l: JurisdictionLevel.STATE

    engine_ext._escalate_grievance(g, EscalationReason.SLA_BREACH, db_session, "Second escalation")

    audit2 = db_session.query(EscalationAudit).order_by(EscalationAudit.id.desc()).first()
    assert audit2.id != audit1.id
    assert audit2.previous_integrity_hash == audit1.integrity_hash

    # Verify via API
    resp1 = client.get(f"/api/audit/{audit1.id}/blockchain-verify")
    assert resp1.status_code == 200
    assert resp1.json()["is_valid"] is True

    resp2 = client.get(f"/api/audit/{audit2.id}/blockchain-verify")
    assert resp2.status_code == 200
    assert resp2.json()["is_valid"] is True

def test_escalation_audit_tamper_detection(client, db_session):
    # Setup
    audit_last_hash_cache.clear()
    j1 = Jurisdiction(level=JurisdictionLevel.LOCAL, geographic_coverage={"cities": ["Pune"]}, responsible_authority="Ward Officer", default_sla_hours=24)
    db_session.add(j1)
    db_session.commit()

    audit = EscalationAudit(
        grievance_id=1,
        previous_authority="A",
        new_authority="B",
        reason=EscalationReason.MANUAL,
        integrity_hash="old_hash",
        previous_integrity_hash=""
    )
    # Manually calculate correct hash
    hash_content = f"1|A|B|manual|"
    audit.integrity_hash = hashlib.sha256(hash_content.encode()).hexdigest()

    db_session.add(audit)
    db_session.commit()

    # Verify initial state
    resp = client.get(f"/api/audit/{audit.id}/blockchain-verify")
    assert resp.json()["is_valid"] is True

    # Tamper with data
    audit.new_authority = "C"
    db_session.commit()

    # Verify tamper detection
    resp = client.get(f"/api/audit/{audit.id}/blockchain-verify")
    assert resp.json()["is_valid"] is False
    assert "Integrity check failed" in resp.json()["message"]

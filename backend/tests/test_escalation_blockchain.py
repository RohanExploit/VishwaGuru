import pytest
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import Base exactly the same way backend.models imports it to avoid duplicate Base instances
from database import Base
from backend.models import Grievance, SeverityLevel, EscalationAudit, EscalationReason, Jurisdiction, JurisdictionLevel, SLAConfig
from backend.grievance_service import GrievanceService
from backend.escalation_engine import EscalationEngine

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

def seed_database(db):
    # Create sample jurisdictions
    jurisdictions_data = [
        {
            "level": JurisdictionLevel.LOCAL,
            "geographic_coverage": {"cities": ["Mumbai"], "districts": ["Mumbai"]},
            "responsible_authority": "Mumbai Municipal Corporation",
            "default_sla_hours": 24
        },
        {
            "level": JurisdictionLevel.DISTRICT,
            "geographic_coverage": {"districts": ["Mumbai", "Pune"], "states": ["Maharashtra"]},
            "responsible_authority": "Maharashtra District Administration",
            "default_sla_hours": 48
        },
        {
            "level": JurisdictionLevel.STATE,
            "geographic_coverage": {"states": ["Maharashtra"]},
            "responsible_authority": "Maharashtra State Government",
            "default_sla_hours": 72
        },
        {
            "level": JurisdictionLevel.NATIONAL,
            "geographic_coverage": {"states": ["Maharashtra", "Karnataka", "Delhi"]},
            "responsible_authority": "Government of India",
            "default_sla_hours": 168  # 1 week
        }
    ]

    for jur_data in jurisdictions_data:
        jurisdiction = Jurisdiction(**jur_data)
        db.add(jurisdiction)

    # Create sample SLA configurations
    sla_configs_data = [
        {
            "severity": SeverityLevel.CRITICAL,
            "jurisdiction_level": JurisdictionLevel.LOCAL,
            "department": "health",
            "sla_hours": 4
        },
        {
            "severity": SeverityLevel.HIGH,
            "jurisdiction_level": JurisdictionLevel.DISTRICT,
            "department": "police",
            "sla_hours": 12
        },
        {
            "severity": SeverityLevel.MEDIUM,
            "jurisdiction_level": JurisdictionLevel.STATE,
            "department": "education",
            "sla_hours": 48
        },
        {
            "severity": SeverityLevel.LOW,
            "jurisdiction_level": JurisdictionLevel.NATIONAL,
            "department": "infrastructure",
            "sla_hours": 168
        }
    ]

    for sla_data in sla_configs_data:
        sla_config = SLAConfig(**sla_data)
        db.add(sla_config)

    db.commit()

@pytest.fixture(name="db_session")
def fixture_db_session():
    # Set up in-memory sqlite with static pool so connections share state
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def clear_hash_cache():
    # Clear in-memory hash cache before and after each test case
    EscalationEngine._audit_last_hash_cache.clear()
    yield
    EscalationEngine._audit_last_hash_cache.clear()

def test_escalation_blockchain_creation_and_verification(db_session):
    """
    Test that EscalationAudit records are correctly created with blockchain-style
    integrity hashes and previous integrity hashes, and can be verified.
    """
    # 1. Initialize the system
    seed_database(db_session)

    service = GrievanceService()

    # 2. Create a test grievance
    grievance_data = {
        "category": "health",
        "severity": "medium",
        "city": "Mumbai",
        "district": "Mumbai",
        "state": "Maharashtra",
        "description": "Public health hazard reported"
    }

    grievance = service.create_grievance(grievance_data, db=db_session)
    assert grievance is not None

    # Retrieve grievance with loaded relationships
    grievance = service.get_grievance(grievance.id, db=db_session)
    assert grievance is not None

    # Clear cache to simulate starting clean (will fetch from DB if needed)
    EscalationEngine._audit_last_hash_cache.clear()

    # 3. Perform first escalation (Severity Escalation)
    success = service.escalate_grievance_severity(
        grievance.id,
        SeverityLevel.CRITICAL,
        reason="Upgrading severity to Critical due to urgent conditions",
        db=db_session
    )
    assert success is True

    # Retrieve audit logs
    audit_logs = db_session.query(EscalationAudit).filter(EscalationAudit.grievance_id == grievance.id).all()
    assert len(audit_logs) == 1
    audit1 = audit_logs[0]

    # Check blockchain fields of first audit
    assert audit1.integrity_hash is not None
    assert audit1.previous_integrity_hash is None

    # Verify first hash: SHA256(grievance_id | reason.value | 'GENESIS')
    expected_hash_input1 = f"{grievance.id}|{audit1.reason.value}|GENESIS"
    expected_hash1 = hashlib.sha256(expected_hash_input1.encode()).hexdigest()
    assert audit1.integrity_hash == expected_hash1

    # Verify integrity verification endpoint/method
    verification1 = service.verify_audit_integrity(audit1.id, db=db_session)
    assert verification1["is_valid"] is True
    assert verification1["message"] == "Integrity verified"

    # Verify that the cache now contains this hash (O(1) lookup check)
    assert EscalationEngine._audit_last_hash_cache[grievance.id] == expected_hash1

    # 4. Perform second escalation (Manual Escalation)
    success2 = service.manual_escalate(
        grievance.id,
        reason="Urgent administrative escalation",
        db=db_session
    )
    assert success2 is True

    # Retrieve updated audit logs
    audit_logs2 = db_session.query(EscalationAudit).filter(EscalationAudit.grievance_id == grievance.id).order_by(EscalationAudit.id).all()
    assert len(audit_logs2) == 2
    audit2 = audit_logs2[1]

    # Check blockchain fields of second audit
    assert audit2.integrity_hash is not None
    assert audit2.previous_integrity_hash == audit1.integrity_hash

    # Verify second hash: SHA256(grievance_id | reason.value | audit1.integrity_hash)
    expected_hash_input2 = f"{grievance.id}|{audit2.reason.value}|{audit1.integrity_hash}"
    expected_hash2 = hashlib.sha256(expected_hash_input2.encode()).hexdigest()
    assert audit2.integrity_hash == expected_hash2

    # Verify integrity of second record
    verification2 = service.verify_audit_integrity(audit2.id, db=db_session)
    assert verification2["is_valid"] is True

    # 5. Tamper Detection Test
    # If someone tampers with the reason or the previous hash, verification must fail.
    # Let's modify the reason of the second audit record in the DB
    audit2.reason = EscalationReason.SLA_BREACH  # changed from MANUAL
    db_session.commit()

    verification_tampered = service.verify_audit_integrity(audit2.id, db=db_session)
    assert verification_tampered["is_valid"] is False
    assert verification_tampered["message"] == "INTEGRITY BREACH DETECTED"

def test_cache_miss_fallback(db_session):
    """
    Test that if the cache is empty, the system falls back to fetching from database
    and successfully continues the hash chain without issues.
    """
    seed_database(db_session)

    service = GrievanceService()
    grievance_data = {
        "category": "police",
        "severity": "medium",
        "city": "Mumbai",
        "district": "Mumbai",
        "state": "Maharashtra",
        "description": "Noise complaint"
    }

    grievance = service.create_grievance(grievance_data, db=db_session)
    assert grievance is not None

    # First escalation
    service.escalate_grievance_severity(
        grievance.id,
        SeverityLevel.CRITICAL,
        reason="Noise level rose significantly",
        db=db_session
    )

    # Verify cache is populated
    assert grievance.id in EscalationEngine._audit_last_hash_cache
    first_hash = EscalationEngine._audit_last_hash_cache[grievance.id]

    # Explicitly clear the in-memory cache to force a DB query (cache miss fallback)
    EscalationEngine._audit_last_hash_cache.clear()

    # Second escalation should query DB, find first_hash, chain it correctly, and re-cache
    service.manual_escalate(
        grievance.id,
        reason="Forced manual escalation",
        db=db_session
    )

    audit_logs = db_session.query(EscalationAudit).filter(EscalationAudit.grievance_id == grievance.id).order_by(EscalationAudit.id).all()
    assert len(audit_logs) == 2
    assert audit_logs[1].previous_integrity_hash == first_hash
    assert EscalationEngine._audit_last_hash_cache[grievance.id] == audit_logs[1].integrity_hash

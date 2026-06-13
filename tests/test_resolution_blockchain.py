"""
Verification tests for Resolution Evidence Blockchain Chaining (Issue #292)
"""

import os
import sys
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import Base
from backend.models import Grievance, ResolutionProofToken, ResolutionEvidence, Jurisdiction, JurisdictionLevel, SeverityLevel, VerificationStatus, GrievanceStatus
from backend.resolution_proof_service import ResolutionProofService
from backend.cache import resolution_last_hash_cache

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create a jurisdiction
    jurisdiction = Jurisdiction(
        level=JurisdictionLevel.LOCAL,
        geographic_coverage={"states": ["Maharashtra"]},
        responsible_authority="Ward A",
        default_sla_hours=24
    )
    db.add(jurisdiction)
    db.commit()
    db.refresh(jurisdiction)

    # Create a grievance
    grievance = Grievance(
        unique_id=f"TEST-{uuid.uuid4().hex[:8]}",
        category="Road",
        severity=SeverityLevel.HIGH,
        current_jurisdiction_id=jurisdiction.id,
        assigned_authority="Ward A",
        sla_deadline=datetime.now(timezone.utc) + timedelta(days=1),
        latitude=19.0760,
        longitude=72.8777,
        status=GrievanceStatus.OPEN
    )
    db.add(grievance)
    db.commit()
    db.refresh(grievance)

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        resolution_last_hash_cache.clear()

def test_evidence_chaining(db):
    """Test that multiple evidence submissions are correctly chained."""
    grievance = db.query(Grievance).first()

    # 1. Generate Token
    token = ResolutionProofService.generate_proof_token(
        grievance_id=grievance.id,
        authority_email="officer@test.com",
        db=db
    )

    # 2. Submit First Evidence
    evidence1_hash = hashlib.sha256(b"image1").hexdigest()
    ev1 = ResolutionProofService.submit_evidence(
        token_id=token.token_id,
        evidence_hash=evidence1_hash,
        gps_latitude=19.0760,
        gps_longitude=72.8777,
        capture_timestamp=datetime.now(timezone.utc),
        db=db
    )

    assert ev1.previous_integrity_hash == ""
    assert ev1.integrity_hash is not None

    # 3. Submit Second Evidence (New Token Needed)
    token2 = ResolutionProofService.generate_proof_token(
        grievance_id=grievance.id,
        authority_email="officer@test.com",
        db=db
    )

    evidence2_hash = hashlib.sha256(b"image2").hexdigest()
    ev2 = ResolutionProofService.submit_evidence(
        token_id=token2.token_id,
        evidence_hash=evidence2_hash,
        gps_latitude=19.0760,
        gps_longitude=72.8777,
        capture_timestamp=datetime.now(timezone.utc),
        db=db
    )

    assert ev2.previous_integrity_hash == ev1.integrity_hash
    assert ev2.integrity_hash != ev1.integrity_hash

def test_o1_verification(db):
    """Test O(1) single record verification logic."""
    grievance = db.query(Grievance).first()

    token = ResolutionProofService.generate_proof_token(
        grievance_id=grievance.id,
        authority_email="officer@test.com",
        db=db
    )

    ev_hash = hashlib.sha256(b"image_o1").hexdigest()
    ev = ResolutionProofService.submit_evidence(
        token_id=token.token_id,
        evidence_hash=ev_hash,
        gps_latitude=19.0760,
        gps_longitude=72.8777,
        capture_timestamp=datetime.now(timezone.utc),
        db=db
    )

    # Verify using service method (which uses O(1) fetch)
    result = ResolutionProofService.verify_evidence(grievance.id, db)
    assert result["is_verified"] is True
    assert result["blockchain_integrity"] is True

def test_tamper_detection(db):
    """Test that tampering with evidence data breaks the integrity check."""
    grievance = db.query(Grievance).first()

    token = ResolutionProofService.generate_proof_token(
        grievance_id=grievance.id,
        authority_email="officer@test.com",
        db=db
    )

    ev_hash = hashlib.sha256(b"original_image").hexdigest()
    ev = ResolutionProofService.submit_evidence(
        token_id=token.token_id,
        evidence_hash=ev_hash,
        gps_latitude=19.0760,
        gps_longitude=72.8777,
        capture_timestamp=datetime.now(timezone.utc),
        db=db
    )

    # Tamper with the evidence hash in DB
    ev.evidence_hash = hashlib.sha256(b"tampered_image").hexdigest()
    db.commit()

    # Verify should now fail blockchain integrity
    result = ResolutionProofService.verify_evidence(grievance.id, db)
    assert result["is_verified"] is False
    assert result["blockchain_integrity"] is False

def test_cache_optimization(db):
    """Test that cache is used and updated correctly."""
    grievance = db.query(Grievance).first()

    # Reset cache
    resolution_last_hash_cache.clear()

    token = ResolutionProofService.generate_proof_token(
        grievance_id=grievance.id,
        authority_email="officer@test.com",
        db=db
    )

    ev_hash = hashlib.sha256(b"cache_test").hexdigest()

    # First submission - cache miss, should populate cache
    with patch.object(resolution_last_hash_cache, 'get', wraps=resolution_last_hash_cache.get) as mock_get:
        ev = ResolutionProofService.submit_evidence(
            token_id=token.token_id,
            evidence_hash=ev_hash,
            gps_latitude=19.0760,
            gps_longitude=72.8777,
            capture_timestamp=datetime.now(timezone.utc),
            db=db
        )
        assert mock_get.called

    assert resolution_last_hash_cache.get("last_hash") == ev.integrity_hash

    # Second submission - should hit cache
    token2 = ResolutionProofService.generate_proof_token(
        grievance_id=grievance.id,
        authority_email="officer@test.com",
        db=db
    )

    ev_hash2 = hashlib.sha256(b"cache_test_2").hexdigest()
    with patch.object(resolution_last_hash_cache, 'get', return_value=ev.integrity_hash) as mock_get_hit:
        ev2 = ResolutionProofService.submit_evidence(
            token_id=token2.token_id,
            evidence_hash=ev_hash2,
            gps_latitude=19.0760,
            gps_longitude=72.8777,
            capture_timestamp=datetime.now(timezone.utc),
            db=db
        )
        assert mock_get_hit.called
        assert ev2.previous_integrity_hash == ev.integrity_hash

if __name__ == "__main__":
    pytest.main([__file__])

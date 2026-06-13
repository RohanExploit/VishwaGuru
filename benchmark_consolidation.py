
import os
import sys
from datetime import datetime, timezone, timedelta
import hashlib
import json
import hmac
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup path
sys.path.insert(0, os.path.abspath(os.getcwd()))

from backend.models import Base, Grievance, ResolutionProofToken, GrievanceStatus, ResolutionEvidence, EvidenceAuditLog, SeverityLevel
from backend.resolution_proof_service import ResolutionProofService
from backend.config import get_config

# Create in-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def test_transaction_consolidation():
    db = TestingSessionLocal()

    # 1. Setup mock grievance and token
    grievance = Grievance(
        unique_id="TEST-G",
        category="Road",
        severity=SeverityLevel.MEDIUM,
        latitude=19.0,
        longitude=72.0,
        current_jurisdiction_id=1,
        assigned_authority="MCGM",
        sla_deadline=datetime.now(timezone.utc),
        status=GrievanceStatus.OPEN
    )
    db.add(grievance)
    db.commit()
    db.refresh(grievance)

    token = ResolutionProofToken(
        token_id="test-token",
        grievance_id=grievance.id,
        authority_email="officer@test.com",
        geofence_latitude=19.0,
        geofence_longitude=72.0,
        geofence_radius_meters=100.0,
        valid_from=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc) + timedelta(minutes=15),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        is_used=False,
        token_signature="test-sig",
        nonce="test-nonce"
    )
    # Re-sign token for validation
    payload = {
        "token_id": "test-token",
        "grievance_id": grievance.id,
        "authority_email": "officer@test.com",
        "geofence_lat": 19.0,
        "geofence_lon": 72.0,
        "geofence_radius": 100.0,
        "valid_from": token.valid_from.isoformat(),
        "valid_until": token.valid_until.isoformat(),
        "nonce": "test-nonce"
    }
    key = get_config().secret_key
    token.token_signature = hmac.new(
            key.encode("utf-8"),
            json.dumps(payload, sort_keys=True).encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    db.add(token)
    db.commit()

    # Monkeypatch db.commit to count calls
    original_commit = db.commit
    commit_count = 0
    def counted_commit():
        nonlocal commit_count
        commit_count += 1
        return original_commit()
    db.commit = counted_commit

    # 2. Submit evidence
    evidence_hash = hashlib.sha256(b"test-evidence").hexdigest()

    print("Submitting evidence...")
    evidence = ResolutionProofService.submit_evidence(
        token_id="test-token",
        evidence_hash=evidence_hash,
        gps_latitude=19.0,
        gps_longitude=72.0,
        capture_timestamp=datetime.now(timezone.utc),
        db=db
    )

    print(f"Total commits during submit_evidence: {commit_count}")

    # Should be exactly 1 commit now (consolidated)
    assert commit_count == 1, f"Expected 1 commit, but got {commit_count}"

    # Verify audit logs were created
    audits = db.query(EvidenceAuditLog).filter(EvidenceAuditLog.evidence_id == evidence.id).order_by(EvidenceAuditLog.id).all()
    assert len(audits) == 2, f"Expected 2 audit logs, got {len(audits)}"

    # Verify blockchain chain in audits
    audit1 = audits[0]
    audit2 = audits[1]

    print(f"Audit 1 hash: {audit1.integrity_hash}")
    print(f"Audit 2 prev hash: {audit2.previous_integrity_hash}")

    assert audit2.previous_integrity_hash == audit1.integrity_hash, "Blockchain chain broken in audit logs"
    assert audit2.integrity_hash is not None

    print("Transaction consolidation and blockchain chaining verified!")
    db.close()

if __name__ == "__main__":
    try:
        test_transaction_consolidation()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

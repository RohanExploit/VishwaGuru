import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta

from backend.main import app
from backend.database import Base, get_db, engine
from backend.models import Grievance, GrievanceStatus, SeverityLevel, GrievanceFollower, Jurisdiction, JurisdictionLevel, ClosureConfirmation
from backend.closure_service import ClosureService

# Setup test database
@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(name="client")
def fixture_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_closure_confirmation_blockchain_chaining(client, db_session):
    # 1. Setup a grievance and followers
    jurisdiction = Jurisdiction(
        level=JurisdictionLevel.LOCAL,
        geographic_coverage={"cities": ["Mumbai"]},
        responsible_authority="BMC",
        default_sla_hours=24
    )
    db_session.add(jurisdiction)
    db_session.flush()

    grievance = Grievance(
        unique_id="TEST-123",
        category="Water",
        severity=SeverityLevel.HIGH,
        current_jurisdiction_id=jurisdiction.id,
        assigned_authority="BMC",
        sla_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
        status=GrievanceStatus.OPEN
    )
    db_session.add(grievance)
    db_session.flush()

    followers = [
        GrievanceFollower(grievance_id=grievance.id, user_email=f"user{i}@example.com")
        for i in range(5)
    ]
    for f in followers:
        db_session.add(f)
    db_session.commit()

    # 2. Request closure
    ClosureService.request_closure(grievance.id, db_session)

    # 3. Submit multiple confirmations and verify chaining
    emails = [f"user{i}@example.com" for i in range(3)]
    conf_ids = []

    for email in emails:
        result = ClosureService.submit_confirmation(
            grievance_id=grievance.id,
            user_email=email,
            confirmation_type="confirmed",
            reason="Verified resolved",
            db=db_session
        )

        # Get the record to check hashes
        conf = db_session.query(ClosureConfirmation).filter(
            ClosureConfirmation.user_email == email,
            ClosureConfirmation.grievance_id == grievance.id
        ).first()
        conf_ids.append(conf.id)

    # Verify the chain
    conf1 = db_session.query(ClosureConfirmation).filter(ClosureConfirmation.id == conf_ids[0]).first()
    conf2 = db_session.query(ClosureConfirmation).filter(ClosureConfirmation.id == conf_ids[1]).first()
    conf3 = db_session.query(ClosureConfirmation).filter(ClosureConfirmation.id == conf_ids[2]).first()

    assert conf1.previous_integrity_hash == ""
    assert conf2.previous_integrity_hash == conf1.integrity_hash
    assert conf3.previous_integrity_hash == conf2.integrity_hash

    # 4. Verify via API endpoint
    for cid in conf_ids:
        response = client.get(f"/api/closure-confirmation/{cid}/blockchain-verify")
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert "Integrity verified" in data["message"]

    # 5. Tamper with data and verify failure
    conf2.confirmation_type = "disputed"
    db_session.commit()

    response = client.get(f"/api/closure-confirmation/{conf_ids[1]}/blockchain-verify")
    assert response.status_code == 200
    assert response.json()["is_valid"] is False
    assert "Integrity check failed" in response.json()["message"]

    # Subsequent record should still be valid if its OWN data and recorded previous_integrity_hash match.
    # Blockchain integrity check for a single record only verifies that IT matches its seal.
    # To detect a break in the chain, you would need to verify the previous record as well.
    # This is consistent with O(1) single-record verification.
    response = client.get(f"/api/closure-confirmation/{conf_ids[2]}/blockchain-verify")
    assert response.status_code == 200
    assert response.json()["is_valid"] is True

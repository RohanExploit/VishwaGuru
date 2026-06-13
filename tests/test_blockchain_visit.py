import os
import sys
import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, os.getcwd())

from backend.database import SessionLocal, engine, Base
from backend.models import FieldOfficerVisit, Issue, Jurisdiction, JurisdictionLevel
from backend.routers.field_officer import officer_check_in, verify_visit_blockchain_integrity
from backend.schemas import OfficerCheckInRequest
from backend.cache import visit_last_hash_cache

def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create a jurisdiction if none exists
    jurisdiction = db.query(Jurisdiction).first()
    if not jurisdiction:
        jurisdiction = Jurisdiction(
            level=JurisdictionLevel.LOCAL,
            geographic_coverage={"districts": ["Test"]},
            responsible_authority="Test Auth",
            default_sla_hours=24
        )
        db.add(jurisdiction)
        db.commit()
        db.refresh(jurisdiction)

    # Create an issue
    issue = Issue(
        description="Test Issue for Blockchain",
        category="Road",
        latitude=18.5204,
        longitude=73.8567,
        status="open"
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)

    return db, issue, jurisdiction

def test_blockchain_chaining():
    db, issue, jurisdiction = setup_db()
    visit_last_hash_cache.clear()

    try:
        print("--- Testing Visit 1 (Initial) ---")
        request1 = OfficerCheckInRequest(
            issue_id=issue.id,
            officer_email="officer1@example.com",
            officer_name="Officer One",
            check_in_latitude=18.5205,
            check_in_longitude=73.8568
        )
        visit1 = officer_check_in(request1, db)
        print(f"Visit 1 Hash: {visit1.visit_hash}")
        print(f"Visit 1 Prev Hash: '{visit1.previous_visit_hash}'")
        assert visit1.previous_visit_hash == ""

        # Verify Visit 1
        verify1 = verify_visit_blockchain_integrity(visit1.id, db)
        print(f"Visit 1 Integrity: {verify1.is_valid}")
        assert verify1.is_valid is True

        print("\n--- Testing Visit 2 (Chained) ---")
        request2 = OfficerCheckInRequest(
            issue_id=issue.id,
            officer_email="officer2@example.com",
            officer_name="Officer Two",
            check_in_latitude=18.5206,
            check_in_longitude=73.8569
        )
        visit2 = officer_check_in(request2, db)
        print(f"Visit 2 Hash: {visit2.visit_hash}")
        print(f"Visit 2 Prev Hash: {visit2.previous_visit_hash}")
        assert visit2.previous_visit_hash == visit1.visit_hash

        # Verify Visit 2
        verify2 = verify_visit_blockchain_integrity(visit2.id, db)
        print(f"Visit 2 Integrity: {verify2.is_valid}")
        assert verify2.is_valid is True

        print("\n--- Testing Tamper Detection ---")
        # Manually tamper with Visit 2 notes in DB
        db_visit2 = db.query(FieldOfficerVisit).filter(FieldOfficerVisit.id == visit2.id).first()
        db_visit2.visit_notes = "TAMPERED NOTES"
        db.commit()

        verify2_tampered = verify_visit_blockchain_integrity(visit2.id, db)
        print(f"Visit 2 Integrity after tampering: {verify2_tampered.is_valid}")
        assert verify2_tampered.is_valid is False
        print("Tamper detection works!")

        print("\n--- Testing Cache O(1) Behavior ---")
        # Clear cache and see if it falls back to DB correctly
        visit_last_hash_cache.clear()
        request3 = OfficerCheckInRequest(
            issue_id=issue.id,
            officer_email="officer3@example.com",
            officer_name="Officer Three",
            check_in_latitude=18.5207,
            check_in_longitude=73.8570
        )
        visit3 = officer_check_in(request3, db)
        print(f"Visit 3 Prev Hash (from DB fallback): {visit3.previous_visit_hash}")
        assert visit3.previous_visit_hash == visit2.visit_hash

        print("\nAll blockchain verification tests PASSED!")

    finally:
        db.close()

if __name__ == "__main__":
    test_blockchain_chaining()

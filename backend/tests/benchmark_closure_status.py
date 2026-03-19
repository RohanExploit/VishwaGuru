import time
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Grievance, GrievanceFollower, ClosureConfirmation, Jurisdiction, JurisdictionLevel, SeverityLevel
from backend.routers.grievances import get_closure_status

# In-memory SQLite for testing
engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def seed_data(db):
    jurisdiction = Jurisdiction(
        level=JurisdictionLevel.LOCAL,
        geographic_coverage={"states": ["Maharashtra"]},
        responsible_authority="Municipal Corporation",
        default_sla_hours=72,
    )
    db.add(jurisdiction)
    db.commit()
    db.refresh(jurisdiction)

    grievance = Grievance(
        unique_id="G123",
        category="pothole",
        severity=SeverityLevel.MEDIUM,
        current_jurisdiction_id=jurisdiction.id,
        assigned_authority="Municipal Corporation",
        sla_deadline=datetime.utcnow() + timedelta(hours=72),
        pincode="123456",
        city="city",
        district="district",
        state="state",
    )
    db.add(grievance)
    db.commit()
    db.refresh(grievance)

    # Add followers
    for i in range(100):
        db.add(GrievanceFollower(grievance_id=grievance.id, user_email=f"user{i}@test.com"))

    # Add confirmations
    for i in range(50):
        db.add(ClosureConfirmation(
            grievance_id=grievance.id,
            user_email=f"cuser{i}@test.com",
            confirmation_type="confirmed" if i % 2 == 0 else "disputed"
        ))

    db.commit()
    return grievance.id

def run_benchmark():
    db = TestingSessionLocal()
    gid = seed_data(db)

    start = time.perf_counter()
    for _ in range(100):
        get_closure_status(grievance_id=gid, db=db)
    end = time.perf_counter()

    print(f"Time taken for 100 calls: {(end - start) * 1000:.2f} ms")
    db.close()

if __name__ == '__main__':
    run_benchmark()

import time
from sqlalchemy.orm import Session
from sqlalchemy import func, create_engine
from backend.models import Base
from backend.models import Grievance, GrievanceFollower, ClosureConfirmation, Issue, Jurisdiction, JurisdictionLevel, SeverityLevel
from sqlalchemy import case, distinct
import datetime

# Create a temporary in-memory database for testing
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)
SessionLocal = Session(bind=engine)

def populate_db(db: Session, grievance_id: int):
    # Add Jurisdiction
    j = Jurisdiction(id=1, level=JurisdictionLevel.STATE, geographic_coverage={"states": ["Maharashtra"]}, responsible_authority="PWD", default_sla_hours=48)
    db.add(j)

    # Add Grievance
    g = Grievance(
        id=grievance_id,
        current_jurisdiction_id=1,
        sla_deadline=datetime.datetime.now(datetime.timezone.utc),
        status="open",
        category="Road",
        unique_id="123",
        severity=SeverityLevel.LOW,
        assigned_authority="PWD"
    )
    db.add(g)

    # Add Followers
    for i in range(50):
        db.add(GrievanceFollower(grievance_id=grievance_id, user_email=f"user{i}@test.com"))

    # Add Confirmations
    for i in range(30):
        db.add(ClosureConfirmation(grievance_id=grievance_id, user_email=f"conf_user{i}@test.com", confirmation_type="confirmed"))
    for i in range(10):
        db.add(ClosureConfirmation(grievance_id=grievance_id, user_email=f"disp_user{i}@test.com", confirmation_type="disputed"))

    db.commit()

def benchmark_old(db: Session, grievance_id: int, iterations=1000):
    start = time.perf_counter()
    for _ in range(iterations):
        total_followers = db.query(func.count(GrievanceFollower.id)).filter(
            GrievanceFollower.grievance_id == grievance_id
        ).scalar()

        counts = db.query(
            ClosureConfirmation.confirmation_type,
            func.count(ClosureConfirmation.id)
        ).filter(ClosureConfirmation.grievance_id == grievance_id).group_by(ClosureConfirmation.confirmation_type).all()

        counts_dict = {ctype: count for ctype, count in counts}
        confirmations_count = counts_dict.get("confirmed", 0)
        disputes_count = counts_dict.get("disputed", 0)
    end = time.perf_counter()
    if iterations > 10:
        print(f"Old approach ({iterations} iters): {end - start:.4f}s")
    return total_followers, confirmations_count, disputes_count

def benchmark_new_agg(db: Session, grievance_id: int, iterations=1000):
    start = time.perf_counter()
    for _ in range(iterations):
        total_followers = db.query(func.count(GrievanceFollower.id)).filter(
            GrievanceFollower.grievance_id == grievance_id
        ).scalar()

        # Re-optimized: use group_by as it is faster for categorical columns
        counts = db.query(
            ClosureConfirmation.confirmation_type,
            func.count(ClosureConfirmation.id)
        ).filter(ClosureConfirmation.grievance_id == grievance_id).group_by(ClosureConfirmation.confirmation_type).all()

        confirmations_count = 0
        disputes_count = 0
        for confirmation_type, count in counts:
            if confirmation_type == 'confirmed':
                confirmations_count = count
            elif confirmation_type == 'disputed':
                disputes_count = count
    end = time.perf_counter()
    if iterations > 10:
        print(f"New approach (Agg) ({iterations} iters): {end - start:.4f}s")
    return total_followers, confirmations_count, disputes_count

if __name__ == "__main__":
    db = SessionLocal
    populate_db(db, 1)

    # Warm up
    benchmark_old(db, 1, 10)
    benchmark_new_agg(db, 1, 10)

    res_old = benchmark_old(db, 1)
    res_agg = benchmark_new_agg(db, 1)

    print(f"Old Results: {res_old}")
    print(f"New Agg Results: {res_agg}")

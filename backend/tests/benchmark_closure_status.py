import time
import uuid
import random
from datetime import datetime, timezone
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from backend.models import Base, Grievance, GrievanceFollower, ClosureConfirmation, Jurisdiction, JurisdictionLevel, SeverityLevel, GrievanceStatus
from backend.database import get_db

# Create an in-memory SQLite database
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

def setup_data(session):
    auth = Jurisdiction(
        level=JurisdictionLevel.LOCAL,
        geographic_coverage={"states": ["Maharashtra"], "districts": ["Mumbai"]},
        responsible_authority="Test Auth",
        default_sla_hours=24
    )
    session.add(auth)
    session.commit()

    grievances = []
    for i in range(10):
        g = Grievance(
            unique_id=f"G-{i}",
            category="Roads",
            severity=SeverityLevel.MEDIUM,
            status=GrievanceStatus.OPEN,
            pincode="123456",
            current_jurisdiction_id=auth.id,
            assigned_authority="Test Auth",
            sla_deadline=datetime.now(timezone.utc)
        )
        session.add(g)
        grievances.append(g)
    session.commit()

    for g in grievances:
        # Add followers
        for j in range(50):
            f = GrievanceFollower(grievance_id=g.id, user_email=f"user{j}@test.com")
            session.add(f)

        # Add confirmations
        for j in range(20):
            c = ClosureConfirmation(grievance_id=g.id, user_email=f"conf{j}@test.com", confirmation_type="confirmed")
            session.add(c)

        # Add disputes
        for j in range(5):
            d = ClosureConfirmation(grievance_id=g.id, user_email=f"disp{j}@test.com", confirmation_type="disputed")
            session.add(d)

    session.commit()
    return grievances

def original_get_closure_status(session, grievance_id):
    from sqlalchemy import func

    total_followers = session.query(func.count(GrievanceFollower.id)).filter(
        GrievanceFollower.grievance_id == grievance_id
    ).scalar()

    confirmations_count = session.query(func.count(ClosureConfirmation.id)).filter(
        ClosureConfirmation.grievance_id == grievance_id,
        ClosureConfirmation.confirmation_type == "confirmed"
    ).scalar()

    disputes_count = session.query(func.count(ClosureConfirmation.id)).filter(
        ClosureConfirmation.grievance_id == grievance_id,
        ClosureConfirmation.confirmation_type == "disputed"
    ).scalar()

    return total_followers, confirmations_count, disputes_count

def optimized_get_closure_status(session, grievance_id):
    from sqlalchemy import func, case

    total_followers = session.query(func.count(GrievanceFollower.id)).filter(
        GrievanceFollower.grievance_id == grievance_id
    ).scalar()

    # Consolidate multiple aggregate queries into a single database roundtrip
    stats = session.query(
        ClosureConfirmation.confirmation_type,
        func.count(ClosureConfirmation.id)
    ).filter(ClosureConfirmation.grievance_id == grievance_id).group_by(ClosureConfirmation.confirmation_type).all()

    confirmations_count = 0
    disputes_count = 0
    for t, c in stats:
        if t == "confirmed":
            confirmations_count = c
        elif t == "disputed":
            disputes_count = c

    return total_followers, confirmations_count, disputes_count

def run_benchmark():
    session = SessionLocal()
    grievances = setup_data(session)

    g_id = grievances[0].id

    # Warmup
    for _ in range(10):
        original_get_closure_status(session, g_id)
        optimized_get_closure_status(session, g_id)

    ITERATIONS = 500

    start_time = time.time()
    for _ in range(ITERATIONS):
        res1 = original_get_closure_status(session, g_id)
    original_time = time.time() - start_time

    start_time = time.time()
    for _ in range(ITERATIONS):
        res2 = optimized_get_closure_status(session, g_id)
    optimized_time = time.time() - start_time

    print(f"Original results: {res1}")
    print(f"Optimized results: {res2}")
    assert res1 == res2, "Results don't match!"

    print(f"Original method: {original_time:.4f} seconds ({original_time/ITERATIONS:.5f} per call)")
    print(f"Optimized method: {optimized_time:.4f} seconds ({optimized_time/ITERATIONS:.5f} per call)")
    print(f"Improvement: {(original_time - optimized_time) / original_time * 100:.2f}%")

if __name__ == "__main__":
    run_benchmark()

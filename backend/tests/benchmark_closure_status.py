import sys
import time
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath('.'))

from backend.database import Base, get_db
from backend.models import Grievance, GrievanceFollower, ClosureConfirmation
from backend.routers.grievances import get_closure_status
from backend.closure_service import ClosureService
from unittest.mock import patch, MagicMock

# In-memory SQLite for testing
engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def seed_data(db):
    grievance = Grievance(
        unique_id="G123",
        category="pothole",
        status="open",
        description="test",
        pincode="123456",
        city="city",
        district="district",
        state="state"
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

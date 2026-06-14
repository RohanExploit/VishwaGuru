import sys
import os
import time

# Add the root directory to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, FieldOfficerVisit
from backend.routers.field_officer import get_visit_statistics
from datetime import datetime, timezone

# Setup SQLite in memory
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def seed_db(db):
    for i in range(100):
        v = FieldOfficerVisit(
            issue_id=1,
            officer_email=f"officer{i%5}@example.com",
            officer_name=f"Officer {i%5}",
            check_in_latitude=0.0,
            check_in_longitude=0.0,
            check_in_time=datetime.now(timezone.utc),
            within_geofence=(i % 2 == 0),
            distance_from_site=10.5,
            status="verified" if i % 3 == 0 else "pending",
            verified_at=datetime.now(timezone.utc) if i % 3 == 0 else None,
            is_public=True
        )
        db.add(v)
    db.commit()

db = TestingSessionLocal()
seed_db(db)

# Run benchmark
start = time.perf_counter()
for _ in range(100):
    get_visit_statistics(db=db)
end = time.perf_counter()

print(f"Time taken for 100 executions: {end - start:.4f} seconds")

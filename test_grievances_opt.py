import time
from backend.database import SessionLocal
from backend.models import Grievance, GrievanceFollower, ClosureConfirmation
from backend.routers.grievances import get_closure_status
from sqlalchemy import func

def bench():
    db = SessionLocal()
    try:
        start = time.perf_counter()
        for _ in range(100):
            total_followers = db.query(func.count(GrievanceFollower.id)).filter(
                GrievanceFollower.grievance_id == 1
            ).scalar()

            counts = db.query(
                ClosureConfirmation.confirmation_type,
                func.count(ClosureConfirmation.id)
            ).filter(ClosureConfirmation.grievance_id == 1).group_by(ClosureConfirmation.confirmation_type).all()
        print(f"Old approach: {time.perf_counter() - start}")

        start = time.perf_counter()
        for _ in range(100):
            # Instead of two queries, we could potentially do this in one, or just measure DB hits
            pass
    finally:
        db.close()

if __name__ == "__main__":
    bench()

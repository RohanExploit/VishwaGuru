import sys
import time
import os

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import func

Base = declarative_base()

class ClosureConfirmation(Base):
    __tablename__ = 'closure_confirmations'
    id = Column(Integer, primary_key=True)
    grievance_id = Column(Integer)
    confirmation_type = Column(String)

engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def seed_data(db):
    grievance_id = 1
    # Add confirmations
    for i in range(1000):
        db.add(ClosureConfirmation(
            grievance_id=grievance_id,
            confirmation_type="confirmed" if i % 2 == 0 else "disputed"
        ))
    db.commit()
    return grievance_id

def run_benchmark():
    db = TestingSessionLocal()
    gid = seed_data(db)

    # Original way
    start = time.perf_counter()
    for _ in range(100):
        confirmations_count = db.query(func.count(ClosureConfirmation.id)).filter(
            ClosureConfirmation.grievance_id == gid,
            ClosureConfirmation.confirmation_type == "confirmed"
        ).scalar()

        disputes_count = db.query(func.count(ClosureConfirmation.id)).filter(
            ClosureConfirmation.grievance_id == gid,
            ClosureConfirmation.confirmation_type == "disputed"
        ).scalar()
    end = time.perf_counter()
    print(f"Original Time taken: {(end - start) * 1000:.2f} ms")

    # Optimized way using group_by
    start2 = time.perf_counter()
    for _ in range(100):
        stats = db.query(
            ClosureConfirmation.confirmation_type,
            func.count(ClosureConfirmation.id)
        ).filter(
            ClosureConfirmation.grievance_id == gid
        ).group_by(
            ClosureConfirmation.confirmation_type
        ).all()

        c_count = 0
        d_count = 0
        for c_type, count in stats:
            if c_type == "confirmed":
                c_count = count
            elif c_type == "disputed":
                d_count = count
    end2 = time.perf_counter()
    print(f"Optimized Time taken: {(end2 - start2) * 1000:.2f} ms")

    db.close()

if __name__ == '__main__':
    run_benchmark()

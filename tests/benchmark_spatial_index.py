import time
import random
import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, Column, Integer, String, Float, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# Define a local Base and Model to ensure we start WITHOUT indexes
# regardless of what's in backend/models.py
Base = declarative_base()

class BenchmarkIssue(Base):
    __tablename__ = "benchmark_issues"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="open", index=True)
    # Explicitly NO indexes on lat/lon for the baseline
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

def run_benchmark():
    print("⚡ Bolt Spatial Index Benchmark ⚡")

    # Use in-memory SQLite with StaticPool to share connection
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create table (without lat/lon indexes)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    print("Generating 10,000 issues...")
    # Insert 10,000 issues
    # Spread them around a center point (e.g., Mumbai 19.0760, 72.8777)
    # +/- 0.1 degree is roughly +/- 11km
    issues = []
    for i in range(10000):
        lat = 19.0760 + random.uniform(-0.1, 0.1)
        lon = 72.8777 + random.uniform(-0.1, 0.1)
        issues.append(BenchmarkIssue(latitude=lat, longitude=lon, status="open"))

    db.add_all(issues)
    db.commit()
    print("Data inserted.")

    # Define query parameters
    target_lat = 19.0760
    target_lon = 72.8777
    # 0.005 degrees is roughly 500m
    min_lat = target_lat - 0.005
    max_lat = target_lat + 0.005
    min_lon = target_lon - 0.005
    max_lon = target_lon + 0.005

    query_sql = text("""
        SELECT count(*) FROM benchmark_issues
        WHERE status = 'open'
        AND latitude >= :min_lat AND latitude <= :max_lat
        AND longitude >= :min_lon AND longitude <= :max_lon
    """)

    # Warmup
    db.execute(query_sql, {"min_lat": min_lat, "max_lat": max_lat, "min_lon": min_lon, "max_lon": max_lon})

    # Measure BEFORE
    start_time = time.time()
    for _ in range(100):
        db.execute(query_sql, {"min_lat": min_lat, "max_lat": max_lat, "min_lon": min_lon, "max_lon": max_lon})
    end_time = time.time()
    avg_time_before = (end_time - start_time) / 100
    print(f"Average query time (NO INDEX): {avg_time_before * 1000:.4f} ms")

    # Add Indexes
    print("Adding indexes...")
    db.execute(text("CREATE INDEX ix_benchmark_issues_latitude ON benchmark_issues (latitude)"))
    db.execute(text("CREATE INDEX ix_benchmark_issues_longitude ON benchmark_issues (longitude)"))
    db.commit()

    # Analyze to ensure stats are updated (SQLite specific)
    db.execute(text("ANALYZE"))

    # Measure AFTER
    start_time = time.time()
    for _ in range(100):
        db.execute(query_sql, {"min_lat": min_lat, "max_lat": max_lat, "min_lon": min_lon, "max_lon": max_lon})
    end_time = time.time()
    avg_time_after = (end_time - start_time) / 100
    print(f"Average query time (WITH INDEX): {avg_time_after * 1000:.4f} ms")

    improvement = (avg_time_before - avg_time_after) / avg_time_before * 100
    print(f"Improvement: {improvement:.2f}%")

    if avg_time_after < avg_time_before:
        print("✅ SUCCESS: Indexing improved performance.")
    else:
        print("❌ FAILURE: No improvement observed.")

if __name__ == "__main__":
    run_benchmark()

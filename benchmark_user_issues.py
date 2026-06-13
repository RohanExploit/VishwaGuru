import time
import json
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db, Base, engine, SessionLocal
from backend.models import Issue, User
import statistics

def setup_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Create 50 issues for a test user
    for i in range(50):
        issue = Issue(
            description=f"Issue {i} description that is somewhat long and should be truncated in the summary response",
            category="Road",
            user_email="test@example.com",
            status="open"
        )
        db.add(issue)
    db.commit()
    db.close()

def benchmark():
    client = TestClient(app)
    url = "/issues/user?user_email=test@example.com&limit=10"

    # Warm up cache
    client.get(url)

    # Benchmark cache hit
    hit_times = []
    for _ in range(100):
        start = time.perf_counter()
        client.get(url)
        hit_times.append(time.perf_counter() - start)

    avg_hit = statistics.mean(hit_times) * 1000
    print(f"Average Cache Hit Time: {avg_hit:.4f}ms")

    # Benchmark cache miss (by clearing)
    from backend.cache import user_issues_cache
    miss_times = []
    for _ in range(20):
        user_issues_cache.clear()
        start = time.perf_counter()
        client.get(url)
        miss_times.append(time.perf_counter() - start)

    avg_miss = statistics.mean(miss_times) * 1000
    print(f"Average Cache Miss Time: {avg_miss:.4f}ms")

    print(f"Speedup: {avg_miss/avg_hit:.2f}x")

if __name__ == "__main__":
    setup_data()
    benchmark()

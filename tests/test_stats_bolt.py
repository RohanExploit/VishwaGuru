from fastapi.testclient import TestClient
from backend.main import app
from backend.database import engine, Base, SessionLocal
from backend.models import Issue

client = TestClient(app)

def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Add some dummy data
    db.add(Issue(description="Issue 1", category="Road", status="open"))
    db.add(Issue(description="Issue 2", category="Road", status="resolved"))
    db.add(Issue(description="Issue 3", category="Water", status="verified"))
    db.commit()
    db.close()

def test_get_stats():
    setup_db()
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_issues"] == 3
    assert data["resolved_issues"] == 2
    assert data["pending_issues"] == 1
    assert data["issues_by_category"]["Road"] == 2
    print("Stats Response:", data)

if __name__ == "__main__":
    try:
        test_get_stats()
        print("Stats verification successful!")
    except Exception as e:
        print(f"Stats verification failed: {e}")
        import traceback
        traceback.print_exc()

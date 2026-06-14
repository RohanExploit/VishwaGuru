from fastapi.testclient import TestClient
from backend.main import app
from backend.database import engine, Base, SessionLocal
from backend.models import Issue

client = TestClient(app)

def test_duplicate_creation():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.query(Issue).delete()
    db.commit()

    # Create original issue via API
    resp1 = client.post("/api/issues", data={
        "description": "Original Pothole report",
        "category": "Road",
        "latitude": 19.0,
        "longitude": 72.0
    })
    assert resp1.status_code == 201
    orig_id = resp1.json()["id"]

    orig = db.query(Issue).get(orig_id)
    orig_hash = orig.integrity_hash

    # Create duplicate via API
    resp2 = client.post("/api/issues", data={
        "description": "Duplicate report",
        "category": "Road",
        "latitude": 19.00001,
        "longitude": 72.00001
    })
    assert resp2.status_code == 201

    # Check DB for duplicate record
    dup = db.query(Issue).filter(Issue.status == "duplicate").first()
    assert dup is not None
    assert dup.parent_issue_id == orig_id
    assert dup.previous_integrity_hash == orig_hash
    print(f"Duplicate record found in DB! Prev Hash: {dup.previous_integrity_hash[:10]}...")

    # Verify original upvotes increased
    db.refresh(orig)
    assert orig.upvotes == 1
    print("Original issue upvoted!")

if __name__ == "__main__":
    test_duplicate_creation()

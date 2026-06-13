import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.database import Base, get_db
from backend.models import Issue, User, UserRole, FieldOfficerVisit
from backend.geofencing_service import generate_visit_hash
import hashlib

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_blockchain.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_field_officer_blockchain_chaining():
    client = TestClient(app)
    db = TestingSessionLocal()

    # 1. Create a test issue
    issue = Issue(
        description="Pothole on Main St",
        category="Road",
        latitude=18.5204,
        longitude=73.8567,
        status="open"
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)

    # 2. Perform first check-in
    checkin1_data = {
        "issue_id": issue.id,
        "officer_email": "officer1@example.com",
        "officer_name": "Officer One",
        "check_in_latitude": 18.5204,
        "check_in_longitude": 73.8567,
        "visit_notes": "First visit"
    }
    response1 = client.post("/api/field-officer/check-in", json=checkin1_data)
    assert response1.status_code == 200
    visit1 = response1.json()
    hash1 = visit1.get("visit_hash")

    # Check if previous_visit_hash exists in response
    assert "previous_visit_hash" in visit1, "previous_visit_hash should be in the response"
    assert visit1["previous_visit_hash"] == "" or visit1["previous_visit_hash"] is None, "First visit should have empty or None previous hash"

    # 3. Perform second check-in
    checkin2_data = {
        "issue_id": issue.id,
        "officer_email": "officer2@example.com",
        "officer_name": "Officer Two",
        "check_in_latitude": 18.5205,
        "check_in_longitude": 73.8568,
        "visit_notes": "Second visit"
    }
    response2 = client.post("/api/field-officer/check-in", json=checkin2_data)
    assert response2.status_code == 200
    visit2 = response2.json()
    hash2 = visit2.get("visit_hash")

    assert "previous_visit_hash" in visit2
    assert visit2["previous_visit_hash"] == hash1, "Second visit should link to first visit's hash"

    # 4. Verify O(1) integrity endpoint
    verify_response = client.get(f"/api/field-officer/{visit2['id']}/blockchain-verify")
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert verify_data["is_valid"] is True
    assert verify_data["current_hash"] == hash2

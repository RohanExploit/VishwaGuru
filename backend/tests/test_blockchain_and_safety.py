import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import Base, get_db
from backend.main import app
from backend.models import Issue

# Setup in-memory SQLite DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    # Create tables
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    # Drop tables
    Base.metadata.drop_all(bind=engine)

def test_safety_score(client):
    # 1. Create a dummy issue (Garbage - Medium Severity)
    response = client.post(
        "/api/issues",
        data={
            "description": "Test Garbage Issue Description",
            "category": "Garbage",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "location": "Pune",
            "language": "en"
        }
    )
    assert response.status_code == 201, f"Response: {response.text}"

    # 2. Get safety score for the same location
    response = client.get(
        "/api/location/safety-score",
        params={"latitude": 18.5204, "longitude": 73.8567, "radius": 500}
    )
    assert response.status_code == 200
    data = response.json()

    # Base score 100 - Garbage(5) = 95
    assert data["score"] == 95
    assert data["label"] == "Safe"
    assert data["issue_count"] == 1

    # 3. Add another issue (Road - Default Severity 5)
    # Ensure it's not deduplicated (move away > 50m)
    # 0.0006 deg lat is approx 66m
    response = client.post(
        "/api/issues",
        data={
            "description": "Test Road Issue Description",
            "category": "Road",
            "latitude": 18.5211,
            "longitude": 73.8567,
            "location": "Pune",
            "language": "en"
        }
    )
    assert response.status_code == 201, f"Response: {response.text}"

    # 4. Get safety score again (radius 500 covers both)
    response = client.get(
        "/api/location/safety-score",
        params={"latitude": 18.5204, "longitude": 73.8567, "radius": 500}
    )
    assert response.status_code == 200
    data = response.json()

    # 95 - Road(5) = 90
    assert data["score"] == 90
    assert data["label"] == "Safe"
    assert data["issue_count"] == 2

def test_blockchain_verification(client):
    # 1. Create first issue (Genesis)
    response1 = client.post(
        "/api/issues",
        data={
            "description": "Genesis Issue Description",
            "category": "Garbage",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "location": "Mumbai",
            "language": "en"
        }
    )
    assert response1.status_code == 201
    issue1_id = response1.json()["id"]

    # 2. Create second issue (Should link to Genesis)
    # Move further away to avoid deduplication (> 50m)
    # 0.001 deg is ~111m
    response2 = client.post(
        "/api/issues",
        data={
            "description": "Second Issue Description",
            "category": "Water",
            "latitude": 19.0780,
            "longitude": 72.8777,
            "location": "Mumbai",
            "language": "en"
        }
    )
    assert response2.status_code == 201, f"Response: {response2.text}"
    issue2_id = response2.json()["id"]

    assert issue2_id is not None, "Issue 2 should have an ID (not deduplicated)"

    # 3. Verify Issue 2
    response_verify = client.get(f"/api/issues/{issue2_id}/blockchain-verify")
    assert response_verify.status_code == 200
    data = response_verify.json()

    assert data["is_valid"] == True
    assert "Integrity verified" in data["message"]

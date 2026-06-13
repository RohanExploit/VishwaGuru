import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import hashlib

from backend.database import Base, get_db
from backend.main import app
from backend.models import Grievance, Jurisdiction, JurisdictionLevel, SeverityLevel, GrievanceFollower, GrievanceStatus
from backend.cache import follower_last_hash_cache
from datetime import datetime, timezone

# Setup in-memory SQLite database for testing
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

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create a jurisdiction
    j = Jurisdiction(
        id=1,
        level=JurisdictionLevel.STATE,
        geographic_coverage={"states": ["Maharashtra"]},
        responsible_authority="PWD",
        default_sla_hours=48
    )
    db.add(j)

    # Create a grievance
    g = Grievance(
        id=1,
        unique_id="G123",
        category="Road",
        severity=SeverityLevel.MEDIUM,
        current_jurisdiction_id=1,
        assigned_authority="PWD",
        sla_deadline=datetime.now(timezone.utc),
        status=GrievanceStatus.OPEN
    )
    db.add(g)
    db.commit()
    db.close()

    # Clear cache before each test
    follower_last_hash_cache.clear()

    yield
    Base.metadata.drop_all(bind=engine)

def test_follower_blockchain_chaining():
    client = TestClient(app)

    # 1. Follow grievance (first follower)
    response = client.post(
        "/api/grievances/1/follow",
        json={"user_email": "user1@test.com"}
    )
    assert response.status_code == 200

    # Get the follower record from DB to check hashes
    db = TestingSessionLocal()
    f1 = db.query(GrievanceFollower).filter(GrievanceFollower.user_email == "user1@test.com").first()
    assert f1.previous_integrity_hash == ""
    assert f1.integrity_hash is not None

    # Verify hash(1|user1@test.com|)
    expected_hash1 = hashlib.sha256(f"1|user1@test.com|".encode()).hexdigest()
    assert f1.integrity_hash == expected_hash1

    # 2. Follow grievance (second follower)
    response = client.post(
        "/api/grievances/1/follow",
        json={"user_email": "user2@test.com"}
    )
    assert response.status_code == 200

    f2 = db.query(GrievanceFollower).filter(GrievanceFollower.user_email == "user2@test.com").first()
    assert f2.previous_integrity_hash == expected_hash1

    # Verify hash(1|user2@test.com|expected_hash1)
    expected_hash2 = hashlib.sha256(f"1|user2@test.com|{expected_hash1}".encode()).hexdigest()
    assert f2.integrity_hash == expected_hash2

    # 3. Verify integrity via endpoint
    response = client.get(f"/api/follower/{f2.id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["current_hash"] == expected_hash2

    db.close()

def test_follower_blockchain_cache_utilization():
    client = TestClient(app)

    # Clear cache
    follower_last_hash_cache.clear()

    # 1. First follow - should be a cache miss but then populate it
    client.post("/api/grievances/1/follow", json={"user_email": "user1@test.com"})

    stats = follower_last_hash_cache.get_stats()
    # Depending on implementation, 'get' might be called twice or once.
    # In my implementation, it's called once.
    assert stats["misses"] >= 1

    last_hash = follower_last_hash_cache.get("last_hash")
    assert last_hash is not None

    # 2. Second follow - should be a cache hit
    client.post("/api/grievances/1/follow", json={"user_email": "user2@test.com"})

    stats = follower_last_hash_cache.get_stats()
    assert stats["hits"] >= 1

def test_follower_blockchain_tamper_detection():
    client = TestClient(app)

    # 1. Follow grievance
    client.post("/api/grievances/1/follow", json={"user_email": "user1@test.com"})

    db = TestingSessionLocal()
    f1 = db.query(GrievanceFollower).first()
    follower_id = f1.id

    # 2. Tamper with data
    f1.user_email = "hacker@test.com"
    db.commit()

    # 3. Verify - should fail
    response = client.get(f"/api/follower/{follower_id}/blockchain-verify")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert "check failed" in data["message"].lower()

    db.close()

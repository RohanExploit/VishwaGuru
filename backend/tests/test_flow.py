import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock
import asyncio

# Setup mocks before importing main to avoid side effects if possible,
# but here we mock where they are used.

import sys
from unittest.mock import MagicMock

# Mock heavy dependencies and those not installed in test env
sys.modules["ultralytics"] = MagicMock()
sys.modules["ultralyticsplus"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["telegram"] = MagicMock()
sys.modules["telegram.ext"] = MagicMock()
sys.modules["telegram.error"] = MagicMock()
sys.modules["pywebpush"] = MagicMock()
sys.modules["firebase_admin"] = MagicMock()
sys.modules["sklearn"] = MagicMock()
sys.modules["scipy"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["cv2"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["speech_recognition"] = MagicMock()
sys.modules["googletrans"] = MagicMock()
sys.modules["langdetect"] = MagicMock()
sys.modules["indic_nlp_library"] = MagicMock()
sys.modules["jose"] = MagicMock()
sys.modules["passlib"] = MagicMock()
sys.modules["passlib.context"] = MagicMock()
sys.modules["async_lru"] = MagicMock()

from backend.main import app
from backend.database import Base, get_db
from backend.models import Issue
from backend.schemas import IssueCategory

# Setup test DB
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
def run_around_tests():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_blockchain_integrity_flow():
    transport = ASGITransport(app=app)

    # Mock services to avoid external dependencies
    with patch("backend.routers.issues.rag_service.retrieve", return_value=None), \
         patch("backend.routers.issues.process_action_plan_background"), \
         patch("backend.routers.issues.create_grievance_from_issue_background"), \
         patch("backend.routers.issues.recent_issues_cache") as mock_cache:

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. Create first issue
            print("Creating first issue...")
            response = await ac.post("/api/issues", data={
                "description": "First issue for testing integrity",
                "category": "Road",
                "latitude": 12.0,
                "longitude": 77.0
            })
            assert response.status_code == 201
            data1 = response.json()
            assert data1["id"] is not None
            issue_id1 = data1["id"]

            # 2. Verify first issue integrity
            print(f"Verifying issue {issue_id1}...")
            response = await ac.get(f"/api/issues/{issue_id1}/blockchain-verify")
            assert response.status_code == 200
            verify1 = response.json()
            assert verify1["is_valid"] is True
            assert verify1["message"].startswith("Integrity verified")

            # 3. Create second issue (should link to first)
            print("Creating second issue...")
            response = await ac.post("/api/issues", data={
                "description": "Second issue for testing integrity",
                "category": "Water",
                "latitude": 13.0, # Far away to avoid deduplication
                "longitude": 78.0
            })
            assert response.status_code == 201
            data2 = response.json()
            assert data2["id"] is not None
            issue_id2 = data2["id"]

            # 4. Verify second issue integrity
            print(f"Verifying issue {issue_id2}...")
            response = await ac.get(f"/api/issues/{issue_id2}/blockchain-verify")
            assert response.status_code == 200
            verify2 = response.json()
            assert verify2["is_valid"] is True

            # Check DB state manually to confirm previous_integrity_hash is set
            db = TestingSessionLocal()
            issue2 = db.query(Issue).filter(Issue.id == issue_id2).first()
            assert issue2.previous_integrity_hash is not None
            assert issue2.previous_integrity_hash == verify1["current_hash"]
            db.close()

@pytest.mark.asyncio
async def test_deduplication_flow():
    transport = ASGITransport(app=app)

    with patch("backend.routers.issues.rag_service.retrieve", return_value=None), \
         patch("backend.routers.issues.process_action_plan_background"), \
         patch("backend.routers.issues.create_grievance_from_issue_background"), \
         patch("backend.routers.issues.recent_issues_cache"):

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. Create an issue
            response = await ac.post("/api/issues", data={
                "description": "Original issue",
                "category": "Road",
                "latitude": 10.0,
                "longitude": 10.0
            })
            assert response.status_code == 201
            data1 = response.json()
            original_id = data1["id"]

            # 2. Create a nearby issue (should be deduplicated)
            response = await ac.post("/api/issues", data={
                "description": "Duplicate issue",
                "category": "Road",
                "latitude": 10.0001,
                "longitude": 10.0001
            })
            assert response.status_code == 201
            data2 = response.json()

            # Should have deduplication info
            assert data2["deduplication_info"]["has_nearby_issues"] is True
            assert data2["id"] is None
            assert data2["linked_issue_id"] == original_id

            # Check that original issue got upvoted
            db = TestingSessionLocal()
            issue = db.query(Issue).filter(Issue.id == original_id).first()
            # Initial upvotes 0, +1 from duplicate
            assert issue.upvotes == 1
            db.close()

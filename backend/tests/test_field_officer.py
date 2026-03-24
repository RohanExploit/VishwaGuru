import sys
from unittest.mock import MagicMock

# Mock heavy optional dependencies before importing backend.main
for _mock_module in [
    "google", "google.generativeai",
    "magic",
    "telegram", "telegram.ext",
    "anthropic", "openai",
    "cv2",
    "numpy",
    "sklearn", "sklearn.cluster",
    "transformers",
    "torch",
    "PIL", "PIL.Image",
    "speech_recognition",
    "googletrans",
    "langdetect",
    "pydub",
]:
    sys.modules.setdefault(_mock_module, MagicMock())

import os
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db
from backend.main import app
from backend.models import FieldOfficerVisit, Issue

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_issue_visit_history(db_session, client):
    # Setup test data
    issue = Issue(
        description="Test description",
        category="Pothole",
        status="open",
        latitude=18.5204,
        longitude=73.8567,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    visit = FieldOfficerVisit(
        issue_id=issue.id,
        officer_email="test@officer.com",
        officer_name="Test Officer",
        check_in_latitude=18.5204,
        check_in_longitude=73.8567,
        is_public=True,
    )
    db_session.add(visit)
    db_session.commit()

    response = client.get(f"/api/field-officer/issue/{issue.id}/visit-history")
    assert response.status_code == 200
    data = response.json()
    assert data["total_visits"] == 1
    assert len(data["visits"]) == 1
    assert data["visits"][0]["officer_name"] == "Test Officer"

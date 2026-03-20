import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import FieldOfficerVisit, Issue
from backend.database import get_db

client = TestClient(app)

def test_get_issue_visit_history(db_session):
    # Setup test data
    issue = Issue(
        title="Test Issue",
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
        is_public=True
    )
    db_session.add(visit)
    db_session.commit()

    response = client.get(f"/api/field-officer/issue/{issue.id}/visit-history")
    assert response.status_code == 200
    data = response.json()
    assert data["total_visits"] == 1
    assert len(data["visits"]) == 1
    assert data["visits"][0]["officer_name"] == "Test Officer"

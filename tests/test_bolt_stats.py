import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db, Base, engine
from backend.models import FieldOfficerVisit, User, UserRole
from sqlalchemy.orm import Session
from datetime import datetime, timezone

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    # Mock admin user for stats access
    from backend.dependencies import get_current_admin_user
    app.dependency_overrides[get_current_admin_user] = lambda: User(email="admin@example.com", role=UserRole.ADMIN)

    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}

def test_get_visit_statistics(client, db_session):
    # Add some visits
    v1 = FieldOfficerVisit(
        issue_id=1,
        officer_email="off1@example.com",
        officer_name="Officer 1",
        check_in_latitude=19.0,
        check_in_longitude=72.0,
        check_in_time=datetime.now(timezone.utc),
        verified_at=datetime.now(timezone.utc),
        within_geofence=True,
        distance_from_site=10.5,
        status="verified"
    )
    v2 = FieldOfficerVisit(
        issue_id=2,
        officer_email="off1@example.com",
        officer_name="Officer 1",
        check_in_latitude=19.1,
        check_in_longitude=72.1,
        check_in_time=datetime.now(timezone.utc),
        within_geofence=False,
        distance_from_site=150.0,
        status="checked_in"
    )
    v3 = FieldOfficerVisit(
        issue_id=3,
        officer_email="off2@example.com",
        officer_name="Officer 2",
        check_in_latitude=19.2,
        check_in_longitude=72.2,
        check_in_time=datetime.now(timezone.utc),
        within_geofence=True,
        distance_from_site=20.0,
        status="checked_in"
    )
    db_session.add_all([v1, v2, v3])
    db_session.commit()

    response = client.get("/api/field-officer/visit-stats")
    assert response.status_code == 200
    data = response.json()

    assert data["total_visits"] == 3
    assert data["verified_visits"] == 1
    assert data["within_geofence_count"] == 2
    assert data["outside_geofence_count"] == 1
    assert data["unique_officers"] == 2
    # (10.5 + 150.0 + 20.0) / 3 = 180.5 / 3 = 60.1666... -> 60.17
    assert data["average_distance_from_site"] == 60.17

def test_get_system_stats(client, db_session):
    # UserRole.ADMIN is already imported
    u1 = User(email="admin1@example.com", hashed_password="pw", role=UserRole.ADMIN, is_active=True)
    u2 = User(email="user1@example.com", hashed_password="pw", role=UserRole.USER, is_active=True)
    u3 = User(email="user2@example.com", hashed_password="pw", role=UserRole.USER, is_active=False)

    db_session.add_all([u1, u2, u3])
    db_session.commit()

    response = client.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["total_users"] == 3
    assert data["admin_count"] == 1
    assert data["active_users"] == 2

def test_get_utility_stats(client, db_session):
    from backend.models import Issue
    i1 = Issue(description="Issue 1", category="Road", status="resolved")
    i2 = Issue(description="Issue 2", category="Water", status="open")
    i3 = Issue(description="Issue 3", category="Road", status="verified")

    db_session.add_all([i1, i2, i3])
    db_session.commit()

    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["total_issues"] == 3
    assert data["resolved_issues"] == 2
    assert data["pending_issues"] == 1
    assert data["issues_by_category"]["Road"] == 2
    assert data["issues_by_category"]["Water"] == 1

def test_get_users_admin(client, db_session):
    u1 = User(email="u1@example.com", hashed_password="pw", role=UserRole.USER, is_active=True)
    db_session.add(u1)
    db_session.commit()

    response = client.get("/admin/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(u["email"] == "u1@example.com" for u in data)

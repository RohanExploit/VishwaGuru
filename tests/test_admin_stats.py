"""
Integration tests for GET /admin/stats endpoint.
Verifies that the single-query aggregation returns correct counts for
total_users, admin_count, and active_users across different DB states.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import get_db
from backend.models import User, UserRole, Base
from backend.dependencies import get_current_admin_user
from backend.routers.admin import router


# ---------------------------------------------------------------------------
# Module-level test app (lightweight – does not import the full backend.main)
# ---------------------------------------------------------------------------

_test_app = FastAPI()
_test_app.include_router(router)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_engine():
    """
    Provide an isolated in-memory SQLite engine for each test.
    StaticPool is required so that every session reuses the same in-memory
    connection and can therefore see the tables created by create_all().
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Return a session bound to the isolated test engine."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def mock_admin_user():
    """Return a minimal User object that satisfies the admin dependency."""
    return User(
        id=1,
        email="admin@test.com",
        hashed_password="hashed",
        role=UserRole.ADMIN,
        is_active=True,
    )


@pytest.fixture
def client(db_session, mock_admin_user):
    """TestClient with get_db and get_current_admin_user overridden."""
    _test_app.dependency_overrides[get_db] = lambda: db_session
    _test_app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user
    with TestClient(_test_app) as c:
        yield c
    _test_app.dependency_overrides = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_user(session, email, role=UserRole.USER, is_active=True):
    user = User(email=email, hashed_password="hashed", role=role, is_active=is_active)
    session.add(user)
    session.commit()
    return user


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_stats_empty_database(client):
    """When there are no users, all counts should be zero."""
    response = client.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 0
    assert data["admin_count"] == 0
    assert data["active_users"] == 0


def test_stats_counts_regular_active_user(client, db_session):
    """A single active regular user increments total_users and active_users only."""
    _add_user(db_session, "user1@test.com", role=UserRole.USER, is_active=True)

    response = client.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 1
    assert data["admin_count"] == 0
    assert data["active_users"] == 1


def test_stats_counts_admin_user(client, db_session):
    """An active admin user increments total_users, admin_count, and active_users."""
    _add_user(db_session, "admin2@test.com", role=UserRole.ADMIN, is_active=True)

    response = client.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 1
    assert data["admin_count"] == 1
    assert data["active_users"] == 1


def test_stats_counts_inactive_user(client, db_session):
    """An inactive user increments total_users only."""
    _add_user(db_session, "inactive@test.com", role=UserRole.USER, is_active=False)

    response = client.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 1
    assert data["admin_count"] == 0
    assert data["active_users"] == 0


def test_stats_mixed_users(client, db_session):
    """Mixed set of users is correctly aggregated in a single query."""
    _add_user(db_session, "admin1@test.com", role=UserRole.ADMIN, is_active=True)
    _add_user(db_session, "admin2@test.com", role=UserRole.ADMIN, is_active=False)
    _add_user(db_session, "user1@test.com", role=UserRole.USER, is_active=True)
    _add_user(db_session, "user2@test.com", role=UserRole.USER, is_active=False)
    _add_user(db_session, "user3@test.com", role=UserRole.USER, is_active=True)

    response = client.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 5
    assert data["admin_count"] == 2   # admin1 + admin2 (active or not)
    assert data["active_users"] == 3  # admin1 + user1 + user3


def test_stats_requires_authentication(db_engine):
    """Endpoint returns 401/403 without admin credentials."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def _get_db_override():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    unauthenticated_app = FastAPI()
    unauthenticated_app.include_router(router)
    unauthenticated_app.dependency_overrides[get_db] = _get_db_override
    # get_current_admin_user is NOT overridden – real auth guard raises 403/422.

    with TestClient(unauthenticated_app, raise_server_exceptions=False) as c:
        response = c.get("/admin/stats")
    assert response.status_code in (401, 403, 422)

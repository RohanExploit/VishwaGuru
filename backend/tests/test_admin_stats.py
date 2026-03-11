"""Unit tests for the GET /admin/stats endpoint (get_system_stats)."""
import sys
from unittest.mock import MagicMock
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Stub heavy optional dependencies that are not needed for this test
for _mod in ("magic", "telegram", "telegram.ext", "google", "google.generativeai", "pywebpush"):
    sys.modules.setdefault(_mod, MagicMock())

from backend.database import Base  # noqa: E402
from backend.models import User, UserRole  # noqa: E402
from backend.routers.admin import get_system_stats  # noqa: E402

# In-memory SQLite database for isolated, fast tests
_ENGINE = create_engine("sqlite://", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=_ENGINE)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE)


@pytest.fixture(autouse=True)
def clean_db():
    """Truncate the users table before each test for isolation."""
    session = _Session()
    session.query(User).delete()
    session.commit()
    session.close()


@pytest.fixture()
def db():
    session = _Session()
    try:
        yield session
    finally:
        session.close()


def _seed_users(session):
    """Seed a known set of users: 5 total, 2 admins, 3 active."""
    users = [
        User(email="admin1@test.com", hashed_password="x", role=UserRole.ADMIN, is_active=True),
        User(email="admin2@test.com", hashed_password="x", role=UserRole.ADMIN, is_active=False),
        User(email="user1@test.com", hashed_password="x", role=UserRole.USER, is_active=True),
        User(email="user2@test.com", hashed_password="x", role=UserRole.USER, is_active=True),
        User(email="user3@test.com", hashed_password="x", role=UserRole.USER, is_active=False),
    ]
    session.add_all(users)
    session.commit()


def test_get_system_stats_empty_db(db):
    """Stats endpoint returns zeros when the database is empty."""
    result = get_system_stats(db=db)
    assert result == {"total_users": 0, "admin_count": 0, "active_users": 0}


def test_get_system_stats_with_users(db):
    """Stats endpoint returns correct aggregate counts for seeded users.

    Seed: 5 users total, 2 admins (1 active + 1 inactive), 3 active users (1 admin + 2 regular).
    """
    _seed_users(db)
    result = get_system_stats(db=db)
    assert result["total_users"] == 5
    assert result["admin_count"] == 2
    assert result["active_users"] == 3


def test_get_system_stats_all_active(db):
    """Stats endpoint counts all users as active when none are deactivated."""
    db.add_all([
        User(email="a@test.com", hashed_password="x", role=UserRole.USER, is_active=True),
        User(email="b@test.com", hashed_password="x", role=UserRole.ADMIN, is_active=True),
    ])
    db.commit()
    result = get_system_stats(db=db)
    assert result["total_users"] == 2
    assert result["admin_count"] == 1
    assert result["active_users"] == 2


def test_get_system_stats_none_active(db):
    """Stats endpoint returns zero active users when all are deactivated."""
    db.add(User(email="inactive@test.com", hashed_password="x", role=UserRole.USER, is_active=False))
    db.commit()
    result = get_system_stats(db=db)
    assert result["total_users"] == 1
    assert result["admin_count"] == 0
    assert result["active_users"] == 0


import pytest
from backend.routers.field_officer import get_visit_statistics
from backend.schemas import VisitStatsResponse
from backend.models import FieldOfficerVisit, Issue
from backend.database import Base, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_get_visit_statistics_empty(test_db):
    stats = get_visit_statistics(db=test_db)
    assert stats is not None
    assert stats.total_visits == 0
    assert stats.verified_visits == 0
    assert stats.within_geofence_count == 0
    assert stats.outside_geofence_count == 0
    assert stats.unique_officers == 0
    assert stats.average_distance_from_site is None

def test_get_visit_statistics_populated(test_db):
    issue = Issue(
        reference_id="ref1", description="desc", latitude=10.0, longitude=10.0,
        image_path="http://example.com/a.jpg", category="Waste", status="open"
    )
    test_db.add(issue)
    test_db.commit()

    visits = [
        FieldOfficerVisit(
            officer_email="a@test.com", officer_name="A", issue_id=issue.id,
            check_in_latitude=10.0, check_in_longitude=10.0,
            distance_from_site=10.0, within_geofence=True, verified_at=datetime.utcnow()
        ),
        FieldOfficerVisit(
            officer_email="a@test.com", officer_name="A", issue_id=issue.id,
            check_in_latitude=10.0, check_in_longitude=10.0,
            distance_from_site=20.0, within_geofence=False, verified_at=None
        ),
        FieldOfficerVisit(
            officer_email="b@test.com", officer_name="B", issue_id=issue.id,
            check_in_latitude=10.0, check_in_longitude=10.0,
            distance_from_site=30.0, within_geofence=True, verified_at=datetime.utcnow()
        ),
    ]
    test_db.add_all(visits)
    test_db.commit()

    stats = get_visit_statistics(db=test_db)
    assert stats.total_visits == 3
    assert stats.verified_visits == 2
    assert stats.within_geofence_count == 2
    assert stats.outside_geofence_count == 1
    assert stats.unique_officers == 2
    assert stats.average_distance_from_site == 20.0

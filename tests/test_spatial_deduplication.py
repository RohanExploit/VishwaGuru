import asyncio
import os
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# Note: This test requires PYTHONPATH=. to be set to import backend modules
# Run with: PYTHONPATH=. python tests/test_spatial_deduplication.py
import sys
import os

from backend.main import app
from backend.models import Base, Issue
from backend.database import engine, SessionLocal
from backend.spatial_utils import find_nearby_issues, haversine_distance

# Setup test DB
Base.metadata.create_all(bind=engine)

def setup_test_issues(db_session):
    """Create test issues with known coordinates for testing deduplication"""

    # Clear existing issues
    db_session.query(Issue).delete()
    db_session.commit()

    # Create test issues in a cluster around Mumbai coordinates
    test_issues = [
        Issue(
            reference_id="test-1",
            description="Pothole on Main Street",
            category="Road",
            status="open",
            latitude=19.0760,
            longitude=72.8777,
            upvotes=2
        ),
        Issue(
            reference_id="test-2",
            description="Another pothole nearby",
            category="Road",
            status="open",
            latitude=19.0761,  # ~11 meters away
            longitude=72.8778,
            upvotes=1
        ),
        Issue(
            reference_id="test-3",
            description="Distant pothole",
            category="Road",
            status="open",
            latitude=19.0860,  # ~1.1 km away
            longitude=72.8877,
            upvotes=0
        ),
        Issue(
            reference_id="test-4",
            description="Resolved issue",
            category="Road",
            status="resolved",
            latitude=19.0760,
            longitude=72.8777,
            upvotes=5
        )
    ]

    for issue in test_issues:
        db_session.add(issue)
    db_session.commit()

    return test_issues

def test_spatial_utils():
    """Test the spatial utility functions"""
    print("Testing spatial utilities...")

    # Test haversine distance
    distance = haversine_distance(19.0760, 72.8777, 19.0761, 72.8778)
    print(f"Distance between test points: {distance:.2f} meters")
    assert 10 <= distance <= 20, f"Expected ~11-15 meters, got {distance}"

    # Test nearby issues finding
    issues = [
        Issue(id=1, latitude=19.0760, longitude=72.8777),
        Issue(id=2, latitude=19.0761, longitude=72.8778),
        Issue(id=3, latitude=19.0860, longitude=72.8877)
    ]

    nearby = find_nearby_issues(issues, 19.0760, 72.8777, radius_meters=50)
    print(f"Found {len(nearby)} nearby issues within 50m")
    assert len(nearby) == 2, f"Expected 2 nearby issues, got {len(nearby)}"

    print("✓ Spatial utilities test passed")

def test_deduplication_api():
    """Test the deduplication API endpoints"""
    print("Testing deduplication API...")

    # Set up test environment
    os.environ["AI_SERVICE_TYPE"] = "mock"

    # Create test database session
    db = SessionLocal()
    try:
        test_issues = setup_test_issues(db)

        # Test nearby issues endpoint
        with TestClient(app) as client:
            response = client.get(
                "/api/issues/nearby",
                params={
                    "latitude": 19.0760,
                    "longitude": 72.8777,
                    "radius": 50,
                    "limit": 10
                }
            )

        print(f"Nearby issues API status: {response.status_code}")
        assert response.status_code == 200

        nearby_data = response.json()
        print(f"Found {len(nearby_data)} nearby issues")
        assert len(nearby_data) >= 2, f"Expected at least 2 nearby issues, got {len(nearby_data)}"

        # Check that issues are sorted by distance
        distances = [issue["distance_meters"] for issue in nearby_data]
        assert distances == sorted(distances), "Issues should be sorted by distance"

        # Test issue creation with deduplication
        with patch("backend.utils.validate_uploaded_file", new_callable=AsyncMock):
            with TestClient(app) as client:
                response = client.post(
                    "/api/issues",
                    data={
                        "description": "Duplicate pothole report",
                        "category": "Road",
                        "latitude": 19.07605,  # Very close to existing issues
                        "longitude": 72.87775,
                        "user_email": "test@example.com"
                    }
                )

        print(f"Create issue API status: {response.status_code}")
        response_data = response.json()
        print(f"Response: {response_data}")

        # Should trigger deduplication
        assert response.status_code == 201
        assert "deduplication_info" in response_data
        assert response_data["deduplication_info"]["has_nearby_issues"] == True
        assert len(response_data["deduplication_info"]["nearby_issues"]) > 0
        assert response_data["linked_issue_id"] is not None

        print("✓ Deduplication API test passed")

    finally:
        db.close()

def test_verification_endpoint():
    """Test the manual verification endpoint"""
    print("Testing verification endpoint...")

    db = SessionLocal()
    try:
        test_issues = setup_test_issues(db)

        # Get the first issue
        issue = test_issues[0]
        original_upvotes = issue.upvotes or 0

        with TestClient(app) as client:
            response = client.post(f"/api/issues/{issue.id}/verify")

        print(f"Verify API status: {response.status_code}")
        assert response.status_code == 200

        response_data = response.json()
        print(f"Verification response: {response_data}")

        # Check that upvotes increased by 2
        assert response_data["upvotes"] == original_upvotes + 2

        # Verify in database
        db.refresh(issue)
        assert issue.upvotes == original_upvotes + 2

        print("✓ Verification endpoint test passed")

    finally:
        db.close()

if __name__ == "__main__":
    print("Running spatial deduplication tests...\n")

    test_spatial_utils()
    print()

    test_deduplication_api()
    print()

    test_verification_endpoint()
    print()

    print("All tests passed! ✓")

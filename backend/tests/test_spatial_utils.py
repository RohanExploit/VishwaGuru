
import pytest
import math
from backend.spatial_utils import haversine_distance, equirectangular_distance, find_nearby_issues
from backend.models import Issue

def test_equirectangular_accuracy_small_distance():
    """Test that equirectangular approximation is accurate for small distances (< 1km)."""
    lat1, lon1 = 18.5204, 73.8567
    # 0.001 degrees is roughly 100 meters
    lat2, lon2 = 18.5214, 73.8577

    h_dist = haversine_distance(lat1, lon1, lat2, lon2)
    e_dist = equirectangular_distance(lat1, lon1, lat2, lon2)

    # Allow 0.1% error margin
    assert abs(h_dist - e_dist) / h_dist < 0.001

def test_equirectangular_accuracy_larger_distance():
    """Test that equirectangular approximation is reasonably accurate for 10km."""
    lat1, lon1 = 18.5204, 73.8567
    # 0.1 degrees is roughly 10km
    lat2, lon2 = 18.6204, 73.9567

    h_dist = haversine_distance(lat1, lon1, lat2, lon2)
    e_dist = equirectangular_distance(lat1, lon1, lat2, lon2)

    # Allow 1% error margin for larger distances (still very good)
    assert abs(h_dist - e_dist) / h_dist < 0.01

def test_find_nearby_issues():
    """Test find_nearby_issues filtering."""
    base_lat, base_lon = 18.5204, 73.8567

    # Create mock issues
    issue_close = Issue(id=1, latitude=base_lat + 0.0001, longitude=base_lon + 0.0001) # Very close
    issue_far = Issue(id=2, latitude=base_lat + 0.1, longitude=base_lon + 0.1) # ~10km away
    issue_exact = Issue(id=3, latitude=base_lat, longitude=base_lon) # Same spot

    issues = [issue_close, issue_far, issue_exact]

    # Radius 50m
    # 0.0001 deg is approx 11m lat, so issue_close is well within 50m
    nearby = find_nearby_issues(issues, base_lat, base_lon, radius_meters=50.0)

    assert len(nearby) == 2
    ids = [i.id for i, _ in nearby]
    assert 3 in ids # Exact match (dist 0)
    assert 1 in ids # Close match
    assert 2 not in ids # Far match

    # Check sorting
    assert nearby[0][0].id == 3 # Closest first
    assert nearby[1][0].id == 1

def test_find_nearby_issues_empty():
    nearby = find_nearby_issues([], 0, 0)
    assert nearby == []

def test_find_nearby_issues_invalid_coords():
    issue = Issue(id=1, latitude=None, longitude=None)
    nearby = find_nearby_issues([issue], 0, 0)
    assert nearby == []

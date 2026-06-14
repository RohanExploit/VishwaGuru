import math
import pytest
from backend.spatial_utils import haversine_distance, find_nearby_issues, equirectangular_distance
from backend.models import Issue
from unittest.mock import Mock

def test_haversine_distance():
    # Test known distance
    # Pune (18.5204, 73.8567) to Mumbai (19.0760, 72.8777)
    # Approx 120 km
    dist = haversine_distance(18.5204, 73.8567, 19.0760, 72.8777)
    assert 118000 < dist < 121000

def test_equirectangular_distance_small_dist():
    # Test small distance (500m) where approximation is good
    lat1, lon1 = 18.5204, 73.8567
    lat2, lon2 = 18.5204 + 0.004, 73.8567 + 0.004 # roughly 600m away

    h_dist = haversine_distance(lat1, lon1, lat2, lon2)
    e_dist = equirectangular_distance(lat1, lon1, lat2, lon2)

    # Expect error less than 1%
    assert abs(h_dist - e_dist) / h_dist < 0.01

def test_equirectangular_distance_dateline():
    # Test crossing dateline
    lat1, lon1 = 0, 179.9
    lat2, lon2 = 0, -179.9

    # Distance should be small (~22km), not huge
    dist = equirectangular_distance(lat1, lon1, lat2, lon2)
    assert 20000 < dist < 25000

def test_find_nearby_issues():
    # Create mock issues
    issue1 = Mock(spec=Issue)
    issue1.latitude = 18.5204
    issue1.longitude = 73.8567
    issue1.id = 1

    issue2 = Mock(spec=Issue)
    issue2.latitude = 18.5205 # Very close
    issue2.longitude = 73.8568
    issue2.id = 2

    issue3 = Mock(spec=Issue)
    issue3.latitude = 19.0760 # Far away (Mumbai)
    issue3.longitude = 72.8777
    issue3.id = 3

    issues = [issue1, issue2, issue3]

    # Search near issue1
    nearby = find_nearby_issues(issues, 18.5204, 73.8567, radius_meters=100)

    # Should find issue1 (dist 0) and issue2 (dist small)
    assert len(nearby) == 2
    assert nearby[0][0].id == 1
    assert nearby[0][1] < 1.0 # Distance 0
    assert nearby[1][0].id == 2
    assert nearby[1][1] < 100.0

    # Search with larger radius to include issue3
    nearby_all = find_nearby_issues(issues, 18.5204, 73.8567, radius_meters=200000)
    assert len(nearby_all) == 3
    # Check sorting
    assert nearby_all[0][0].id == 1
    assert nearby_all[1][0].id == 2
    assert nearby_all[2][0].id == 3

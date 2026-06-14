import pytest
import math
from backend.spatial_utils import haversine_distance, equirectangular_distance, find_nearby_issues
from backend.models import Issue

def test_distance_accuracy_short_range():
    # Two points approx 50m apart in Bangalore
    lat1, lon1 = 12.9716, 77.5946
    lat2, lon2 = 12.9716 + 0.00045, 77.5946 + 0.00045

    h_dist = haversine_distance(lat1, lon1, lat2, lon2)
    e_dist = equirectangular_distance(lat1, lon1, lat2, lon2)

    # Allow for < 0.1% error for short distances
    # For ~70m, error should be negligible
    assert abs(h_dist - e_dist) / h_dist < 0.001

def test_find_nearby_issues_uses_optimization():
    # Setup mock issues
    target_lat, target_lon = 12.9716, 77.5946

    # Issue 1: Very close (~10m)
    i1 = Issue(latitude=12.9716 + 0.00009, longitude=77.5946, id=1)

    # Issue 2: Just within 50m radius
    i2 = Issue(latitude=12.9716 + 0.00040, longitude=77.5946, id=2)

    # Issue 3: Far away
    i3 = Issue(latitude=13.0, longitude=78.0, id=3)

    issues = [i1, i2, i3]

    nearby = find_nearby_issues(issues, target_lat, target_lon, radius_meters=50.0)

    assert len(nearby) == 2
    assert nearby[0][0].id == 1
    assert nearby[1][0].id == 2

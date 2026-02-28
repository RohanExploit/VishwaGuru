import pytest
import math
from unittest.mock import MagicMock, patch
from backend.spatial_utils import haversine_distance, equirectangular_distance, find_nearby_issues, cluster_issues_dbscan
from backend.models import Issue

def test_haversine_vs_equirectangular_accuracy():
    """
    Test that equirectangular approximation is close to Haversine
    for short distances (e.g. < 1km).
    """
    lat1, lon1 = 18.5204, 73.8567
    lat2, lon2 = 18.5205, 73.8568 # Very close ~15m

    d1 = haversine_distance(lat1, lon1, lat2, lon2)
    d2 = equirectangular_distance(lat1, lon1, lat2, lon2)

    # Difference should be negligible for such short distance
    assert abs(d1 - d2) < 0.1, f"Difference too large: {abs(d1 - d2)}"

    # Test slightly larger distance ~10km
    lat3 = lat1 + 0.1 # approx 11km
    d3 = haversine_distance(lat1, lon1, lat3, lon1)
    d4 = equirectangular_distance(lat1, lon1, lat3, lon1)

    # Difference increases but should still be small relative to distance
    assert abs(d3 - d4) < 1.0, f"Difference too large at 10km: {abs(d3 - d4)}"

def test_equirectangular_dateline_wrapping():
    """
    Test that equirectangular distance handles dateline wrapping correctly.
    """
    # Points on opposite sides of dateline
    lat = 0.0
    lon1 = 179.9
    lon2 = -179.9

    # Expected distance: 0.2 degrees * 111km/deg approx 22km
    d = equirectangular_distance(lat, lon1, lat, lon2)

    # Calculate expected roughly
    # dlon = 0.2 degrees
    R = 6371000.0
    expected = (0.2 * math.pi / 180) * R

    assert abs(d - expected) < 100.0, f"Dateline calc failed. Got {d}, expected ~{expected}"

def test_find_nearby_issues_selection(monkeypatch):
    """
    Test that find_nearby_issues selects the correct distance function based on radius.
    """
    # Create mock issues
    issue1 = MagicMock(spec=Issue)
    issue1.latitude = 10.0
    issue1.longitude = 10.0

    issues = [issue1]
    target_lat = 10.0
    target_lon = 10.001 # slightly away

    # Mock the distance functions to verify which one is called
    mock_haversine = MagicMock(return_value=5.0)
    mock_equirect = MagicMock(return_value=5.0)

    monkeypatch.setattr("backend.spatial_utils.haversine_distance", mock_haversine)
    monkeypatch.setattr("backend.spatial_utils.equirectangular_distance", mock_equirect)

    # Case 1: Small radius (default 50m) -> Should use equirectangular
    find_nearby_issues(issues, target_lat, target_lon, radius_meters=50.0)

    assert mock_equirect.called, "Should have called equirectangular_distance for small radius"
    assert not mock_haversine.called, "Should NOT have called haversine_distance for small radius"

    # Reset mocks
    mock_haversine.reset_mock()
    mock_equirect.reset_mock()

    # Case 2: Large radius (> 10km) -> Should use haversine
    find_nearby_issues(issues, target_lat, target_lon, radius_meters=15000.0)

    assert mock_haversine.called, "Should have called haversine_distance for large radius"
    assert not mock_equirect.called, "Should NOT have called equirectangular_distance for large radius"

def test_missing_sklearn_handling(monkeypatch):
    """
    Test that cluster_issues_dbscan handles missing sklearn gracefully.
    Should return individual clusters to preserve data visibility.
    """
    # Mock HAS_SKLEARN to be False
    monkeypatch.setattr("backend.spatial_utils.HAS_SKLEARN", False)

    issue1 = MagicMock(spec=Issue)
    issue1.latitude = 10.0
    issue1.longitude = 10.0

    issue2 = MagicMock(spec=Issue)
    issue2.latitude = None # Invalid coordinate
    issue2.longitude = 10.0

    issues = [issue1, issue2]
    clusters = cluster_issues_dbscan(issues)

    # Should return only valid issues as individual clusters
    assert len(clusters) == 1
    assert len(clusters[0]) == 1
    assert clusters[0][0] == issue1

def test_find_nearby_issues_functional():
    """
    Functional test for find_nearby_issues using real distance calc.
    """
    lat, lon = 18.52, 73.85

    # Issue at exactly same location
    issue1 = Issue(id=1, latitude=lat, longitude=lon)
    # Issue 100m away (approx 0.0009 deg lat)
    issue2 = Issue(id=2, latitude=lat + 0.0009, longitude=lon)
    # Issue 20km away
    issue3 = Issue(id=3, latitude=lat + 0.18, longitude=lon)

    issues = [issue1, issue2, issue3]

    # Radius 200m -> Should include issue1 and issue2, exclude issue3
    # This path uses Equirectangular
    nearby = find_nearby_issues(issues, lat, lon, radius_meters=200.0)

    assert len(nearby) == 2
    assert nearby[0][0].id == 1
    assert nearby[1][0].id == 2
    assert nearby[0][1] < 1.0 # Distance ~0
    assert 90.0 < nearby[1][1] < 110.0 # Distance ~100m

    # Radius 50km -> Should include all
    # This path uses Haversine
    nearby_large = find_nearby_issues(issues, lat, lon, radius_meters=50000.0)
    assert len(nearby_large) == 3
    # Check issue3 is included and distance is roughly 20km (0.18 deg * 111km/deg)
    # 0.18 * 111 = 19.98km
    found_issue3 = next((res for res in nearby_large if res[0].id == 3), None)
    assert found_issue3 is not None
    assert 19000 < found_issue3[1] < 21000

"""
Focused tests for spatial utility functions without API dependencies.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.spatial_utils import (
    haversine_distance,
    equirectangular_distance_squared,
    find_nearby_issues,
    EARTH_RADIUS_METERS
)
from backend.models import Issue
import math


def test_haversine_distance():
    """Test the Haversine distance calculation"""
    print("Testing Haversine distance...")
    
    # Test case 1: Short distance
    distance = haversine_distance(19.0760, 72.8777, 19.0761, 72.8778)
    print(f"  Short distance: {distance:.2f} meters")
    assert 10 <= distance <= 20, f"Expected ~11-15 meters, got {distance}"
    
    # Test case 2: Cross-IDL distance at equator
    cross_idl = haversine_distance(0.0, 179.9, 0.0, -179.9)
    print(f"  Cross-IDL distance (179.9 to -179.9): {cross_idl:.2f} meters")
    assert cross_idl < 25000, f"Expected ~22km, got {cross_idl:.2f}m"
    
    # Test case 3: High latitude cross-IDL (at 60°N, 1° longitude ≈ 55.6km)
    high_lat = haversine_distance(60.0, 179.5, 60.0, -179.5)
    print(f"  High-lat cross-IDL distance (60°N): {high_lat:.2f} meters")
    assert 50000 <= high_lat <= 60000, f"Expected ~55.6km, got {high_lat:.2f}m"
    
    print("✓ Haversine distance tests passed")


def test_equirectangular_vs_haversine():
    """Test that equirectangular approximation is accurate for small distances"""
    print("Testing equirectangular approximation accuracy...")
    
    target_lat, target_lon = 19.0760, 72.8777
    rad_factor = math.pi / 180.0
    target_lat_rad = target_lat * rad_factor
    target_lon_rad = target_lon * rad_factor
    cos_lat = math.cos(target_lat_rad)
    
    # Test at various small distances
    test_points = [
        (19.0761, 72.8778, "~15m"),
        (19.0765, 72.8782, "~60m"),
        (19.0770, 72.8787, "~140m"),
    ]
    
    for lat2, lon2, desc in test_points:
        haversine_dist = haversine_distance(target_lat, target_lon, lat2, lon2)
        
        lat2_rad = lat2 * rad_factor
        lon2_rad = lon2 * rad_factor
        equirect_dist_sq = equirectangular_distance_squared(
            target_lat_rad, target_lon_rad, lat2_rad, lon2_rad, cos_lat
        )
        equirect_dist = math.sqrt(equirect_dist_sq)
        
        error_pct = abs(haversine_dist - equirect_dist) / haversine_dist * 100
        print(f"  {desc}: Haversine={haversine_dist:.2f}m, Equirect={equirect_dist:.2f}m, Error={error_pct:.3f}%")
        
        # For small distances (<200m), error should be negligible (<0.1%)
        if haversine_dist < 200:
            assert error_pct < 0.1, f"Error too large for {desc}: {error_pct:.3f}%"
    
    print("✓ Equirectangular approximation accuracy tests passed")


def test_international_date_line_handling():
    """Test that longitude wrapping works correctly near the International Date Line"""
    print("Testing International Date Line handling...")
    
    # Test case 1: Points near +180/-180 boundary at equator
    issues = [
        Issue(id=1, latitude=0.0, longitude=179.9),
        Issue(id=2, latitude=0.0, longitude=-179.9),
    ]
    
    # Test from eastern side of IDL
    nearby_east = find_nearby_issues(issues, 0.0, 179.9, radius_meters=30000)
    print(f"  Found {len(nearby_east)} issues within 30km from 179.9°E")
    assert len(nearby_east) == 2, f"Expected 2 issues (both sides of IDL), got {len(nearby_east)}"
    
    # Verify distances
    for issue, distance in nearby_east:
        print(f"    Issue {issue.id}: {distance:.2f}m")
    
    # Test case 2: High latitude near IDL (at 60°N, longitude scale is compressed)
    issues_high_lat = [
        Issue(id=3, latitude=60.0, longitude=179.5),
        Issue(id=4, latitude=60.0, longitude=-179.5),
    ]
    
    nearby_high_lat = find_nearby_issues(issues_high_lat, 60.0, 179.5, radius_meters=60000)
    print(f"  Found {len(nearby_high_lat)} issues at 60°N within 60km")
    assert len(nearby_high_lat) == 2, f"Expected 2 issues at high latitude, got {len(nearby_high_lat)}"
    
    for issue, distance in nearby_high_lat:
        print(f"    Issue {issue.id}: {distance:.2f}m")
        if issue.id == 3:
            # Same location as target
            assert distance < 100, f"Same location should be ~0m, got {distance:.2f}m"
        elif issue.id == 4:
            # Verify distance is reasonable (~55.6km across IDL)
            assert 50000 <= distance <= 60000, f"Expected ~55.6km, got {distance:.2f}m"
    
    # Test case 3: Verify IDL wrapping doesn't match distant points
    issues_wrapped = [
        Issue(id=5, latitude=0.0, longitude=179.0),
        Issue(id=6, latitude=0.0, longitude=-179.0),
    ]
    
    # With small radius, shouldn't match across IDL
    nearby_small = find_nearby_issues(issues_wrapped, 0.0, 179.0, radius_meters=250000)
    print(f"  Found {len(nearby_small)} issues within 250km from 179.0°E")
    # Both should be found as they're ~222km apart
    assert len(nearby_small) == 2, f"Expected 2 issues, got {len(nearby_small)}"
    
    for issue, distance in nearby_small:
        print(f"    Issue {issue.id}: {distance:.2f}m")
        if issue.id == 5:
            assert distance < 100, f"Same location should be ~0m, got {distance:.2f}m"
        elif issue.id == 6:
            # At equator, 2° ≈ 222km
            assert 200000 <= distance <= 230000, f"Cross-IDL should be ~222km, got {distance:.2f}m"
    
    print("✓ International Date Line handling tests passed")


def test_find_nearby_issues():
    """Test the nearby issues finding function"""
    print("Testing find_nearby_issues...")
    
    issues = [
        Issue(id=1, latitude=19.0760, longitude=72.8777),
        Issue(id=2, latitude=19.0761, longitude=72.8778),
        Issue(id=3, latitude=19.0860, longitude=72.8877),
    ]
    
    # Test with 50m radius
    nearby = find_nearby_issues(issues, 19.0760, 72.8777, radius_meters=50)
    print(f"  Found {len(nearby)} nearby issues within 50m")
    assert len(nearby) == 2, f"Expected 2 nearby issues, got {len(nearby)}"
    
    # Verify sorting by distance
    assert nearby[0][1] <= nearby[1][1], "Issues should be sorted by distance"
    print(f"  Distances: {[f'{d:.2f}m' for _, d in nearby]}")
    
    # Test with larger radius
    nearby_large = find_nearby_issues(issues, 19.0760, 72.8777, radius_meters=2000)
    print(f"  Found {len(nearby_large)} nearby issues within 2km")
    assert len(nearby_large) == 3, f"Expected 3 nearby issues, got {len(nearby_large)}"
    
    print("✓ find_nearby_issues tests passed")


def test_earth_radius_consistency():
    """Test that EARTH_RADIUS_METERS is used consistently"""
    print("Testing Earth radius constant consistency...")
    
    # Verify the constant is defined
    assert EARTH_RADIUS_METERS == 6371000.0, f"Expected 6371000.0, got {EARTH_RADIUS_METERS}"
    
    # Verify it's being used in haversine
    # We can indirectly test by checking if distance calculations are reasonable
    distance = haversine_distance(0.0, 0.0, 0.0, 1.0)  # 1 degree longitude at equator
    expected = EARTH_RADIUS_METERS * math.radians(1.0)  # ~111km
    
    # Should be close (within 1%)
    error_pct = abs(distance - expected) / expected * 100
    print(f"  1° longitude at equator: {distance:.2f}m (expected ~{expected:.2f}m, error {error_pct:.3f}%)")
    assert error_pct < 1.0, f"Distance calculation seems incorrect, error: {error_pct:.3f}%"
    
    print("✓ Earth radius consistency tests passed")


if __name__ == "__main__":
    print("Running spatial utility tests...\n")
    
    test_haversine_distance()
    print()
    
    test_equirectangular_vs_haversine()
    print()
    
    test_international_date_line_handling()
    print()
    
    test_find_nearby_issues()
    print()
    
    test_earth_radius_consistency()
    print()
    
    print("All tests passed! ✓")

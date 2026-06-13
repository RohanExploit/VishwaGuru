
import pytest
import time
import math
import random
from typing import List, Tuple
from backend.spatial_utils import find_nearby_issues, equirectangular_distance

class MockIssue:
    def __init__(self, id, lat, lon):
        self.id = id
        self.latitude = lat
        self.longitude = lon
        self.upvotes = 0
        self.created_at = time.time()

    def __repr__(self):
        return f"Issue(id={self.id}, lat={self.latitude:.5f}, lon={self.longitude:.5f})"

def reference_find_nearby_issues(
    issues: List[MockIssue],
    target_lat: float,
    target_lon: float,
    radius_meters: float = 50.0
) -> List[Tuple[MockIssue, float]]:
    """
    Reference implementation of find_nearby_issues using the original loop logic.
    """
    nearby_issues = []

    for issue in issues:
        if issue.latitude is None or issue.longitude is None:
            continue

        distance = equirectangular_distance(
            target_lat, target_lon,
            issue.latitude, issue.longitude
        )

        if distance <= radius_meters:
            nearby_issues.append((issue, distance))

    nearby_issues.sort(key=lambda x: x[1])
    return nearby_issues

def test_find_nearby_issues_correctness_and_performance():
    """
    Verify correctness and measure performance improvement.
    """
    target_lat = 40.7128
    target_lon = -74.0060
    radius = 500.0

    # Generate 5000 issues for performance measurement
    issues = []
    random.seed(42) # Deterministic seed
    for i in range(5000):
        # Random offset roughly within 0.02 degrees (~2km)
        lat = target_lat + (random.random() - 0.5) * 0.04
        lon = target_lon + (random.random() - 0.5) * 0.04
        issues.append(MockIssue(i, lat, lon))

    iterations = 20

    # 1. Correctness Check
    # Get results from reference implementation (one run)
    result_ref = reference_find_nearby_issues(issues, target_lat, target_lon, radius)

    # Get results from current/optimized implementation (one run)
    result_curr = find_nearby_issues(issues, target_lat, target_lon, radius)

    # Assert number of results match
    print(f"Count Current: {len(result_curr)}")
    print(f"Count Reference: {len(result_ref)}")

    # Find diffs
    ids_curr = {item[0].id for item in result_curr}
    ids_ref = {item[0].id for item in result_ref}

    only_in_curr = ids_curr - ids_ref
    only_in_ref = ids_ref - ids_curr

    if only_in_curr:
        print(f"Only in current: {only_in_curr}")
        for i in list(only_in_curr)[:3]:
            issue = next(item[0] for item in result_curr if item[0].id == i)
            dist = next(item[1] for item in result_curr if item[0].id == i)
            # Check reference distance
            dist_ref = equirectangular_distance(target_lat, target_lon, issue.latitude, issue.longitude)
            print(f"Issue {i}: Dist calc={dist}, Ref calc={dist_ref}, Radius={radius}")

    if only_in_ref:
        print(f"Only in reference: {only_in_ref}")
        for i in list(only_in_ref)[:3]:
            issue = next(item[0] for item in result_ref if item[0].id == i)
            dist = next(item[1] for item in result_ref if item[0].id == i)
            print(f"Issue {i}: Ref Dist={dist}, Radius={radius}")

    # Allow for very slight floating point differences in inclusion
    # Assert that the sets are almost identical (e.g. at most 1 element diff due to exact boundary)
    diff_count = len(ids_curr.symmetric_difference(ids_ref))
    assert diff_count <= 2, f"Too many differences in result set: {diff_count}"

    # 2. Performance Benchmark
    start_ref = time.time()
    for _ in range(iterations):
        reference_find_nearby_issues(issues, target_lat, target_lon, radius)
    time_ref = time.time() - start_ref

    start_curr = time.time()
    for _ in range(iterations):
        find_nearby_issues(issues, target_lat, target_lon, radius)
    time_curr = time.time() - start_curr

    print(f"\n[Performance] Reference: {time_ref:.4f}s")
    print(f"[Performance] Optimized: {time_curr:.4f}s")

    ratio = time_curr / time_ref if time_ref > 0 else 0
    print(f"[Performance] Ratio (Opt/Ref): {ratio:.2f}")

    if ratio < 0.8:
        print("PASS: Significant performance improvement detected")
    else:
        print("WARN: No significant performance improvement yet (expected before optimization)")

if __name__ == "__main__":
    test_find_nearby_issues_correctness_and_performance()

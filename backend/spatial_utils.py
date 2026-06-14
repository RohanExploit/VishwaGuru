"""
Spatial utilities for geospatial operations and deduplication.
"""
import math
from typing import List, Tuple, Optional
from sklearn.cluster import DBSCAN
import numpy as np

from backend.models import Issue


# Earth's mean radius in meters
# Note: We use the mean radius (6371000m) rather than WGS84 equatorial radius (6378137m)
# because it provides better accuracy across all latitudes, not just at the equator.
# This is the standard choice for general geographic distance calculations.
EARTH_RADIUS_METERS = 6371000.0


def get_bounding_box(lat: float, lon: float, radius_meters: float) -> Tuple[float, float, float, float]:
    """
    Calculate the bounding box coordinates for a given radius.
    Returns (min_lat, max_lat, min_lon, max_lon).
    """
    # Coordinate offsets in radians
    # Prevent division by zero at poles
    effective_lat = max(min(lat, 89.9), -89.9)
    dlat = radius_meters / EARTH_RADIUS_METERS
    dlon = radius_meters / (EARTH_RADIUS_METERS * math.cos(math.pi * effective_lat / 180.0))

    # Offset positions in decimal degrees
    lat_offset = dlat * 180.0 / math.pi
    lon_offset = dlon * 180.0 / math.pi

    min_lat = lat - lat_offset
    max_lat = lat + lat_offset
    min_lon = lon - lon_offset
    max_lon = lon + lon_offset

    return min_lat, max_lat, min_lon, max_lon


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees) using the Haversine formula.

    Returns distance in meters.
    """
    # Convert decimal degrees to radians
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_METERS * c


def equirectangular_distance_squared(
    lat1_rad: float, lon1_rad: float,
    lat2_rad: float, lon2_rad: float,
    cos_lat: float
) -> float:
    """
    Calculate squared equirectangular distance approximation.
    Very accurate for small distances and faster than Haversine.
    Handles longitude wrapping correctly.

    Returns squared distance in meters^2.
    """
    dlon = lon2_rad - lon1_rad

    # Handle longitude wrapping (International Date Line)
    # E.g. 179 to -179 should be 2 degrees, not 358
    if dlon > math.pi:
        dlon -= 2 * math.pi
    elif dlon < -math.pi:
        dlon += 2 * math.pi

    x = dlon * cos_lat * EARTH_RADIUS_METERS
    y = (lat2_rad - lat1_rad) * EARTH_RADIUS_METERS

    return x*x + y*y


def find_nearby_issues(
    issues: List[Issue],
    target_lat: float,
    target_lon: float,
    radius_meters: float = 50.0
) -> List[Tuple[Issue, float]]:
    """
    Find issues within a specified radius of a target location.
    Uses fast equirectangular approximation for pre-filtering candidates,
    then computes accurate Haversine distance for final results.

    Args:
        issues: List of Issue objects to search through
        target_lat: Target latitude
        target_lon: Target longitude
        radius_meters: Search radius in meters (default 50m)

    Returns:
        List of tuples (issue, distance_meters) for issues within radius,
        sorted by distance (closest first). Distance is great-circle (Haversine).
    """
    nearby_issues = []

    # Pre-calculate constants for optimization
    rad_factor = math.pi / 180.0
    target_lat_rad = target_lat * rad_factor
    target_lon_rad = target_lon * rad_factor
    cos_lat = math.cos(target_lat_rad)
    radius_sq = radius_meters * radius_meters

    for issue in issues:
        if issue.latitude is None or issue.longitude is None:
            continue

        # Convert issue coordinates to radians
        lat_rad = issue.latitude * rad_factor
        lon_rad = issue.longitude * rad_factor

        # Fast pre-filter using squared equirectangular distance
        dist_sq = equirectangular_distance_squared(
            target_lat_rad, target_lon_rad,
            lat_rad, lon_rad,
            cos_lat
        )

        if dist_sq <= radius_sq:
            # Calculate accurate great-circle distance for candidates that passed filter
            distance = haversine_distance(target_lat, target_lon, issue.latitude, issue.longitude)
            nearby_issues.append((issue, distance))

    # Sort by distance (closest first)
    nearby_issues.sort(key=lambda x: x[1])

    return nearby_issues


def cluster_issues_dbscan(issues: List[Issue], eps_meters: float = 30.0) -> List[List[Issue]]:
    """
    Cluster issues using DBSCAN algorithm based on spatial proximity.

    Args:
        issues: List of Issue objects with latitude/longitude
        eps_meters: Maximum distance between two samples for one to be considered
                   as in the neighborhood of the other (default 30m)

    Returns:
        List of clusters, where each cluster is a list of Issue objects
    """
    # Filter issues with valid coordinates
    valid_issues = [
        issue for issue in issues
        if issue.latitude is not None and issue.longitude is not None
    ]

    if not valid_issues:
        return []

    # Convert to numpy array for DBSCAN
    coordinates = np.array([
        [issue.latitude, issue.longitude] for issue in valid_issues
    ])

    # Convert eps from meters to degrees (approximate)
    # 1 degree latitude ≈ 111,000 meters
    # 1 degree longitude ≈ 111,000 * cos(latitude) meters
    eps_degrees = eps_meters / 111000  # Rough approximation

    # Perform DBSCAN clustering
    db = DBSCAN(eps=eps_degrees, min_samples=1, metric='haversine').fit(
        np.radians(coordinates)
    )

    # Group issues by cluster
    clusters = {}
    for i, label in enumerate(db.labels_):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(valid_issues[i])

    # Return clusters as list of lists (exclude noise points labeled as -1)
    return [cluster for label, cluster in clusters.items() if label != -1]


def get_cluster_representative(cluster: List[Issue]) -> Issue:
    """
    Get the representative issue from a cluster.
    Uses the issue with the most upvotes, or the oldest if tie.

    Args:
        cluster: List of issues in the same cluster

    Returns:
        Representative issue from the cluster
    """
    if not cluster:
        raise ValueError("Cluster cannot be empty")

    # Sort by upvotes (descending), then by creation date (ascending)
    sorted_issues = sorted(
        cluster,
        key=lambda x: (-(x.upvotes or 0), x.created_at)
    )

    return sorted_issues[0]


def calculate_cluster_centroid(cluster: List[Issue]) -> Tuple[float, float]:
    """
    Calculate the centroid (average position) of a cluster of issues.

    Args:
        cluster: List of issues with coordinates

    Returns:
        Tuple of (latitude, longitude) representing the centroid
    """
    valid_issues = [
        issue for issue in cluster
        if issue.latitude is not None and issue.longitude is not None
    ]

    if not valid_issues:
        raise ValueError("No valid coordinates in cluster")

    avg_lat = sum(issue.latitude for issue in valid_issues) / len(valid_issues)
    avg_lon = sum(issue.longitude for issue in valid_issues) / len(valid_issues)

    return avg_lat, avg_lon

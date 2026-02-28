"""
Spatial utilities for geospatial operations and deduplication.
"""
import math
from typing import List, Tuple, Optional
import logging

try:
    from sklearn.cluster import DBSCAN
    import numpy as np
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    DBSCAN = None
    np = None

from backend.models import Issue

logger = logging.getLogger(__name__)

def get_bounding_box(lat: float, lon: float, radius_meters: float) -> Tuple[float, float, float, float]:
    """
    Calculate the bounding box coordinates for a given radius.
    Returns (min_lat, max_lat, min_lon, max_lon).
    """
    # Earth's radius in meters
    R = 6378137.0

    # Coordinate offsets in radians
    # Prevent division by zero at poles
    effective_lat = max(min(lat, 89.9), -89.9)
    dlat = radius_meters / R
    dlon = radius_meters / (R * math.cos(math.pi * effective_lat / 180.0))

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
    R = 6371000.0  # Earth's radius in meters

    # Convert decimal degrees to radians
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def equirectangular_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two points on the earth (specified in decimal degrees)
    using the Equirectangular approximation. This is faster than Haversine for small distances.

    Returns distance in meters.
    """
    R = 6371000.0  # Earth's radius in meters

    # Convert decimal degrees to radians
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    lon1_rad, lon2_rad = math.radians(lon1), math.radians(lon2)

    # Calculate differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Handle longitude wrapping (dateline crossing)
    # Normalize dlon to [-pi, pi]
    dlon = (dlon + math.pi) % (2 * math.pi) - math.pi

    x = dlon * math.cos((lat1_rad + lat2_rad) / 2)
    y = dlat

    return R * math.sqrt(x*x + y*y)


def find_nearby_issues(
    issues: List[Issue],
    target_lat: float,
    target_lon: float,
    radius_meters: float = 50.0
) -> List[Tuple[Issue, float]]:
    """
    Find issues within a specified radius of a target location.

    Args:
        issues: List of Issue objects to search through
        target_lat: Target latitude
        target_lon: Target longitude
        radius_meters: Search radius in meters (default 50m)

    Returns:
        List of tuples (issue, distance_meters) for issues within radius
    """
    nearby_issues = []

    # Determine which distance function to use based on radius
    # Use Haversine for larger distances (> 10km) where curvature matters more
    # Use Equirectangular for smaller distances for performance (~2.5x faster)
    use_precise = radius_meters > 10000
    distance_func = haversine_distance if use_precise else equirectangular_distance

    for issue in issues:
        if issue.latitude is None or issue.longitude is None:
            continue

        distance = distance_func(
            target_lat, target_lon,
            issue.latitude, issue.longitude
        )

        if distance <= radius_meters:
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
    if not HAS_SKLEARN:
        logger.warning("Scikit-learn not available, returning unclustered issues.")
        # Return each issue as its own cluster to ensure visibility
        return [[issue] for issue in issues if issue.latitude is not None and issue.longitude is not None]

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
    try:
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
    except Exception as e:
        logger.error(f"Error during DBSCAN clustering: {e}")
        return []


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

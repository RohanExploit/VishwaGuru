"""
Geo-Fencing Service for Field Officer Check-In System
Calculates distances and verifies location proximity for officer visits
Issue #288: Field Officer Check-In System With Location Verification
"""

import logging
import hashlib
import hmac
import math
import os
from typing import Tuple, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Get secret key from environment for HMAC
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7").encode('utf-8')

# Earth's radius in meters (mean radius)
EARTH_RADIUS_METERS = 6371000


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth using the Haversine formula.
    
    Args:
        lat1: Latitude of first point (degrees)
        lon1: Longitude of first point (degrees)
        lat2: Latitude of second point (degrees)
        lon2: Longitude of second point (degrees)
        
    Returns:
        Distance in meters
    """
    try:
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        
        distance = EARTH_RADIUS_METERS * c
        
        logger.debug(f"Calculated distance: {distance:.2f}m between ({lat1}, {lon1}) and ({lat2}, {lon2})")
        
        return distance
        
    except Exception as e:
        logger.error(f"Error calculating distance: {e}", exc_info=True)
        return float('inf')  # Return infinity on error to fail geo-fence check


def is_within_geofence(
    check_in_lat: float,
    check_in_lon: float,
    site_lat: float,
    site_lon: float,
    radius_meters: float = 100.0
) -> Tuple[bool, float]:
    """
    Check if a check-in location is within the geo-fence radius of the site.
    
    Args:
        check_in_lat: Check-in latitude
        check_in_lon: Check-in longitude
        site_lat: Site latitude
        site_lon: Site longitude
        radius_meters: Acceptable radius in meters (default: 100m)
        
    Returns:
        Tuple of (within_geofence: bool, distance: float)
    """
    distance = calculate_distance(check_in_lat, check_in_lon, site_lat, site_lon)
    within_fence = distance <= radius_meters
    
    if within_fence:
        logger.info(f"Check-in within geofence: {distance:.2f}m <= {radius_meters}m")
    else:
        logger.warning(f"Check-in OUTSIDE geofence: {distance:.2f}m > {radius_meters}m")
    
    return within_fence, distance


def generate_visit_hash(visit_data: dict) -> str:
    """
    Generate a tamper-resistant HMAC hash for visit data (blockchain-like integrity).
    
    Uses HMAC-SHA256 with server secret to prevent forgery.
    Normalizes datetime to ISO format for deterministic hashing.
    
    Args:
        visit_data: Dictionary containing visit information
        
    Returns:
        HMAC-SHA256 hash of visit data
    """
    try:
        # Normalize check_in_time to ISO format string for determinism
        check_in_time = visit_data.get('check_in_time')
        if isinstance(check_in_time, datetime):
            check_in_time_str = check_in_time.isoformat()
        else:
            check_in_time_str = str(check_in_time) if check_in_time else ""
        
        # Create a deterministic string from visit data
        data_string = (
            f"{visit_data.get('issue_id')}"
            f"{visit_data.get('officer_email')}"
            f"{visit_data.get('check_in_latitude')}"
            f"{visit_data.get('check_in_longitude')}"
            f"{check_in_time_str}"
            f"{visit_data.get('visit_notes', '')}"
        )
        
        # Generate HMAC-SHA256 hash for tamper-resistance
        visit_hash = hmac.new(
            SECRET_KEY,
            data_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        logger.debug(f"Generated visit HMAC hash: {visit_hash[:16]}...")
        
        return visit_hash
        
    except Exception as e:
        logger.error(f"Error generating visit hash: {e}", exc_info=True)
        return ""


def verify_visit_integrity(visit_data: dict, stored_hash: str) -> bool:
    """
    Verify the integrity of visit data against stored hash.
    
    Args:
        visit_data: Dictionary containing visit information
        stored_hash: Previously stored hash
        
    Returns:
        True if data is unmodified, False otherwise
    """
    try:
        computed_hash = generate_visit_hash(visit_data)
        is_valid = computed_hash == stored_hash
        
        if not is_valid:
            logger.warning(f"Visit integrity check FAILED: {computed_hash[:16]}... != {stored_hash[:16]}...")
        else:
            logger.info("Visit integrity check PASSED")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Error verifying visit integrity: {e}", exc_info=True)
        return False


def calculate_visit_metrics(visits: list) -> dict:
    """
    Calculate aggregate metrics for a list of visits.
    
    Args:
        visits: List of visit objects
        
    Returns:
        Dictionary of metrics
    """
    try:
        if not visits:
            return {
                'total_visits': 0,
                'verified_visits': 0,
                'within_geofence_count': 0,
                'outside_geofence_count': 0,
                'unique_officers': 0,
                'average_distance_from_site': None
            }
        
        verified_count = sum(1 for v in visits if v.verified_at is not None)
        within_fence_count = sum(1 for v in visits if v.within_geofence)
        outside_fence_count = len(visits) - within_fence_count
        unique_officers = len(set(v.officer_email for v in visits))
        
        # Calculate average distance (only for visits with distance data)
        distances = [v.distance_from_site for v in visits if v.distance_from_site is not None]
        avg_distance = sum(distances) / len(distances) if distances else None
        
        return {
            'total_visits': len(visits),
            'verified_visits': verified_count,
            'within_geofence_count': within_fence_count,
            'outside_geofence_count': outside_fence_count,
            'unique_officers': unique_officers,
            'average_distance_from_site': round(avg_distance, 2) if avg_distance else None
        }
        
    except Exception as e:
        logger.error(f"Error calculating visit metrics: {e}", exc_info=True)
        # Return valid default metrics to avoid ValidationError in router
        return {
            'total_visits': 0,
            'verified_visits': 0,
            'within_geofence_count': 0,
            'outside_geofence_count': 0,
            'unique_officers': 0,
            'average_distance_from_site': None
        }


class GeoFencingService:
    """Service for geo-fencing operations"""
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> bool:
        """Validate GPS coordinates"""
        return -90 <= latitude <= 90 and -180 <= longitude <= 180
    
    @staticmethod
    def get_distance_description(distance_meters: float) -> str:
        """Get human-readable distance description"""
        if distance_meters < 1:
            return f"{distance_meters * 100:.0f} cm"
        elif distance_meters < 1000:
            return f"{distance_meters:.1f} meters"
        else:
            return f"{distance_meters / 1000:.2f} km"
    
    @staticmethod
    def suggest_geofence_radius(issue_type: str) -> float:
        """
        Suggest appropriate geofence radius based on issue type
        
        Args:
            issue_type: Type of issue (e.g., "Road", "Water", "Garbage")
            
        Returns:
            Suggested radius in meters
        """
        radius_map = {
            "Road": 150.0,  # Roads can be long
            "Water": 100.0,  # Water issues are usually localized
            "Garbage": 75.0,  # Garbage points are specific
            "Streetlight": 50.0,  # Very specific location
            "College Infra": 200.0,  # Campus can be large
            "Women Safety": 100.0  # General area
        }
        
        return radius_map.get(issue_type, 100.0)  # Default 100m


# Singleton service instance
_geofencing_service = None

def get_geofencing_service() -> GeoFencingService:
    """Get or create GeoFencingService singleton"""
    global _geofencing_service
    if _geofencing_service is None:
        _geofencing_service = GeoFencingService()
    return _geofencing_service

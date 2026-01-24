"""
Health check utilities for external API monitoring.
"""

from fastapi import APIRouter
from backend.external_api import monitor_external_services
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/api/health/external")
async def external_services_health():
    """
    Comprehensive health check for all external services.
    Returns detailed status of each external dependency.
    """
    try:
        services_status = await monitor_external_services()
        
        # Calculate overall health
        all_healthy = all(services_status.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": services_status,
            "timestamp": time.time(),
            "details": {
                "total_services": len(services_status),
                "healthy_services": sum(services_status.values()),
                "unhealthy_services": len(services_status) - sum(services_status.values())
            }
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }
"""System health check endpoint."""
import logging
from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime, timezone
from src.config.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

async def check_redis_connection() -> Dict[str, str]:
    """Check Redis connection if enabled."""
    if not settings.get("USE_REDIS_CACHING", False):
        return {"status": "disabled"}

    try:
        from redis import Redis
        redis_url = settings.get("REDIS_URL", "redis://localhost:6379/0")
        redis_client = Redis.from_url(redis_url)
        redis_client.ping()
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@router.get("")
@router.get("/")
async def check_health() -> Dict[str, Any]:
    """
    Health check endpoint.
    Returns system health status and component checks.
    """
    # Check critical dependencies
    redis_health = await check_redis_connection()

    # Aggregate health status
    all_healthy = all(
        check["status"] in ["healthy", "disabled"]
        for check in [redis_health]
    )

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "redis": redis_health,
            # Add more service checks here as needed
        },
        "version": settings.get("APP_VERSION", "1.0.0")
    }
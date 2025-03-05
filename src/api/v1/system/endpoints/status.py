"""System status endpoint for platform diagnostics."""
import psutil
import time
import logging
from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()

# Store start time for uptime calculation
START_TIME = time.time()

@router.get("/", include_in_schema=True)
@router.get("", include_in_schema=True)
async def get_system_status() -> Dict[str, Any]:
    """
    Get overall system diagnostics including resource usage and uptime.
    """
    try:
        # Calculate system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime = time.time() - START_TIME
        
        return {
            "status": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(uptime, 2),
            "resources": {
                "cpu": {
                    "usage_percent": cpu_percent
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used_percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "used_percent": disk.percent
                }
            }
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "status": "error",
            "message": "Failed to retrieve system status",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

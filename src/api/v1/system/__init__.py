"""System endpoints package."""
from fastapi import APIRouter
from .endpoints import status, health, metrics

# Create the system router
router = APIRouter()

# Include the system endpoints
router.include_router(
    status.router,
    prefix="/status",
    tags=["System Status"]
)

router.include_router(
    health.router,
    prefix="/health",
    tags=["System Health"]
)

router.include_router(
    metrics.router,
    prefix="/metrics",
    tags=["System Metrics"]
)
"""Admin endpoints package."""
from fastapi import APIRouter
from .endpoints import config

# Create the admin router
router = APIRouter()

# Include the config management endpoints
router.include_router(
    config.router,
    prefix="/config",
    tags=["Admin Configuration"]
)
"""API v1 package."""
from fastapi import APIRouter
from .admin import router as admin_router
from .system import router as system_router
from .ai import router as ai_router

# Create the v1 router
router = APIRouter()

# Include all sub-routers
router.include_router(admin_router, prefix="/admin", tags=["Administration"])
router.include_router(system_router, prefix="/system", tags=["System"])
router.include_router(ai_router, prefix="/ai", tags=["AI Services"])

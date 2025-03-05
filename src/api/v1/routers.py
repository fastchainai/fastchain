"""Main router for API v1."""
from fastapi import APIRouter
from datetime import datetime
from src.api.v1.agents.intent.endpoints import query, classification
from src.api.v1.agents.chat.endpoints.chat import router as chat_router
from src.api.v1.agents.registry.endpoints import router as registry_router
from src.api.v1.admin import router as admin_router
from src.api.v1.system import router as system_router
from src.utils.logging import Logging

# Initialize logger
logger = Logging(__name__)

# Create the main v1 router
router = APIRouter()

# Health check endpoints for v1 - handle both with and without trailing slash
@router.get("/health")
@router.get("/health/")
async def health_check():
    """Health check endpoint for API v1."""
    logger.info("v1 API health check requested")
    return {
        "status": "healthy",
        "version": "1.0",
        "timestamp": datetime.now().isoformat()
    }

# Include agents endpoints
router.include_router(
    registry_router,
    prefix="/agents/registry",  # Updated prefix to follow domain structure
    tags=["Agent Registry"]
)

# Include chat agent endpoints
router.include_router(
    chat_router,
    prefix="/chat",
    tags=["Chat Agent"]
)

# Include intent agent endpoints
router.include_router(
    query.router,
    prefix="/intent",
    tags=["Intent Processing"]
)

router.include_router(
    classification.router,
    prefix="/intent",
    tags=["Intent Classification"]
)

# Include admin endpoints
router.include_router(
    admin_router,
    prefix="/admin",
    tags=["Administration"]
)

# Include system endpoints
router.include_router(
    system_router,
    prefix="/system",
    tags=["System"]
)

# Log all registered routes
routes = [{"path": route.path, "methods": route.methods} for route in router.routes]
logger.info("v1 API routes registered", extra={"routes": routes})
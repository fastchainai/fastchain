"""Main router configuration for the API."""
from fastapi import FastAPI
from src.api.v1.routers import router as api_v1_router
from src.utils.logging import Logging

# Initialize logger
logger = Logging(__name__)

# Create the main FastAPI app
app = FastAPI(
    title="FastChain AI",
    description="Multi-agent platform combining FastAPI's speed with Langchain's modular chain-based logic",
    version="1.0.0"
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "name": "FastChain AI",
        "version": "1.0.0",
        "description": "FastChain AI API",
        "endpoints": {
            "/": "Root endpoint (this response)",
            "/api/v1": "API version 1",
            "/api/v1/health": "Health check endpoint",
            "/docs": "API documentation",
            "/redoc": "API documentation (ReDoc)"
        }
    }

# Include the v1 router with the correct prefix
app.include_router(api_v1_router, prefix="/api/v1")

# Log initialization and available routes
logger.info("API router initialized with v1 endpoints")
routes = [{"path": route.path, "methods": route.methods} for route in app.routes]
logger.debug("Available routes:", extra={"routes": routes})
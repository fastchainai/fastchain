"""FastAPI application initialization."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.main_router import router as main_router
from src.agents.chat_agent.manager import ChatAgentManager
from fastapi.exceptions import HTTPException
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title="FastChain AI",
    description="FastChain AI - Multi-agent Platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the main router
app.include_router(main_router)

# Initialize the Chat Agent Manager
chat_manager = ChatAgentManager()

@app.on_event("startup")
async def startup_event():
    """Initialize application components on startup."""
    try:
        # Start the Chat Agent
        chat_manager.start()
    except Exception as e:
        print(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    try:
        # Stop the Chat Agent
        chat_manager.stop()
    except Exception as e:
        print(f"Error during shutdown: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "name": "FastChain AI",
        "version": "1.0.0",
        "description": "FastChain AI API",
        "endpoints": {
            "/v1/chat": "Chat endpoints",
            "/v1/intent": "Intent processing endpoints",
            "/v1/admin": "Admin endpoints",
            "/v1/system": "System endpoints"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        agent_status = chat_manager.get_agent_status()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "chat_agent": agent_status
        }
    except Exception as e:
        print(f"Error in health check: {e}")
        return {"status": "unhealthy", "error": str(e)}
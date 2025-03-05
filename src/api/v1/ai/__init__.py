"""AI endpoints package."""
from fastapi import APIRouter
from .endpoints import openai

# Create the AI router
router = APIRouter()

# Include the OpenAI endpoints
router.include_router(
    openai.router,
    prefix="/openai",
    tags=["AI Services"]
)

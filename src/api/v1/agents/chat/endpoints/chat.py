"""Chat endpoints implementation."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime

from src.agents.chat_agent.manager import ChatAgentManager
from src.api.v1.agents.chat.schemas import ChatRequest, ChatResponse

router = APIRouter()
chat_manager = ChatAgentManager()

@router.get("/")
async def get_chat_info():
    """
    Get information about the chat API endpoints.
    """
    return {
        "name": "Chat API",
        "version": "1.0",
        "endpoints": {
            "POST /": "Send a chat message",
            "GET /status": "Get chat agent status",
            "GET /": "This documentation"
        },
        "example_request": {
            "message": "Hello, how are you?",
            "session_id": "optional-session-id"
        }
    }

@router.post("/", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest):
    """
    Process a chat message through the Chat Agent.

    Args:
        request: The chat request containing the message and optional session ID

    Returns:
        ChatResponse: The processed chat response
    """
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="Message is required")

        response = await chat_manager.process_message(
            message=request.message,
            session_id=request.session_id
        )

        return ChatResponse(
            response=response.get("response", ""),
            session_id=response.get("session_id", ""),
            status="success",
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")

@router.get("/status", response_model=Dict[str, Any])
async def get_chat_status():
    """
    Get the current status of the chat agent.

    Returns:
        Dict containing the agent status and timestamp
    """
    try:
        status = chat_manager.get_agent_status()
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat status: {str(e)}")
"""Chat endpoints router implementation."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import datetime

from src.agents.chat_agent.manager import ChatAgentManager
from src.utils.logging import Logging
from src.utils.tracing import SpanContextManager
from .schemas import ChatRequest, ChatResponse, ChatHistoryResponse

# Initialize logger
logger = Logging(__name__)

# Initialize router with prefix and tags
router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize Chat Agent Manager
chat_manager = ChatAgentManager()

@router.post("/", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    """
    Process a chat message.

    Args:
        request: The chat request containing the message and optional session ID

    Returns:
        ChatResponse: The processed chat response
    """
    with SpanContextManager("chat_endpoint") as span:
        try:
            span.set_attribute("session_id", request.session_id or "new_session")

            logger.info(event="chat_request_received",
                       session_id=request.session_id,
                       message_length=len(request.message))

            response = await chat_manager.process_message(
                message=request.message,
                session_id=request.session_id
            )

            return ChatResponse(
                response=response["response"],
                session_id=response["session_id"],
                status=response["status"],
                timestamp=datetime.utcnow().isoformat()
            )

        except Exception as e:
            logger.error(event="chat_processing_failed",
                        error=str(e),
                        session_id=request.session_id,
                        exc_info=True)
            if span:
                span.record_exception(e)
            raise HTTPException(
                status_code=500,
                detail="Error processing chat message"
            )

@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """
    Get chat history for a session.

    Args:
        session_id: The session ID to retrieve history for

    Returns:
        ChatHistoryResponse: The chat history response
    """
    with SpanContextManager("get_chat_history") as span:
        try:
            span.set_attribute("session_id", session_id)

            # Get history from the chat model
            history = chat_manager.agent.chat_model.get_conversation_history()

            return ChatHistoryResponse(
                session_id=session_id,
                history=history,
                timestamp=datetime.utcnow().isoformat()
            )

        except Exception as e:
            logger.error(event="history_retrieval_failed",
                        error=str(e),
                        session_id=session_id,
                        exc_info=True)
            if span:
                span.record_exception(e)
            raise HTTPException(
                status_code=500,
                detail="Error retrieving chat history"
            )

@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Clear chat history for a session.

    Args:
        session_id: The session ID to clear history for

    Returns:
        dict: Success message
    """
    with SpanContextManager("clear_chat_history") as span:
        try:
            span.set_attribute("session_id", session_id)

            # Clear history
            chat_manager.agent.chat_model.clear_conversation_history()

            logger.info(event="chat_history_cleared",
                       session_id=session_id)

            return {"message": "Chat history cleared successfully"}

        except Exception as e:
            logger.error(event="history_clear_failed",
                        error=str(e),
                        session_id=session_id,
                        exc_info=True)
            if span:
                span.record_exception(e)
            raise HTTPException(
                status_code=500,
                detail="Error clearing chat history"
            )
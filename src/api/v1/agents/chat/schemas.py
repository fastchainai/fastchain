"""Chat endpoint schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    """Chat request schema."""
    message: str = Field(..., description="The chat message to process")
    session_id: Optional[str] = Field(None, description="Optional session ID for context continuity")

class ChatResponse(BaseModel):
    """Chat response schema."""
    response: str = Field(..., description="The processed response")
    session_id: str = Field(..., description="The session ID")
    status: str = Field(..., description="The processing status")
    timestamp: str = Field(..., description="The response timestamp")

class ChatHistoryResponse(BaseModel):
    """Chat history response schema."""
    session_id: str = Field(..., description="The session ID")
    history: List[str] = Field(..., description="The chat history")
    timestamp: str = Field(..., description="The response timestamp")

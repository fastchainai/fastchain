"""Schemas for Intent Agent API endpoints."""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class IntentRequest(BaseModel):
    """Schema for intent processing request."""
    query: str = Field(..., description="The input query to process")
    context: Optional[Dict] = Field(default=None, description="Optional context information")

class IntentResponse(BaseModel):
    """Schema for intent processing response."""
    intent: Dict[str, str] = Field(..., description="Classified intent information")
    confidence: float = Field(..., description="Confidence score of the classification")
    entities: Dict[str, List[str]] = Field(default_factory=dict, description="Extracted entities")
    requires_action: bool = Field(default=False, description="Whether this intent requires an action")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata about the processing")

class ClassificationRequest(BaseModel):
    """Schema for intent classification request."""
    text: str = Field(..., description="Text to classify")
    options: Optional[List[str]] = Field(default=None, description="Optional list of intent options")

class ClassificationResponse(BaseModel):
    """Schema for intent classification response."""
    intent: str = Field(..., description="Classified intent name")
    confidence: float = Field(..., description="Classification confidence score")
    alternatives: List[Dict[str, float]] = Field(
        default_factory=list,
        description="Alternative classifications with confidence scores"
    )

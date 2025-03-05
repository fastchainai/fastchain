"""Classification endpoints for Intent Agent."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from src.api.v1.agents.intent.schemas import (
    ClassificationRequest,
    ClassificationResponse
)
from src.api.v1.agents.intent.dependencies import (
    get_intent_agent,
    validate_query_options
)
from src.agents.intent_agent import IntentAgent

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.post("/classify", response_model=ClassificationResponse)
async def classify_intent(
    request: ClassificationRequest,
    agent: IntentAgent = Depends(get_intent_agent),
    options: list = Depends(validate_query_options)
) -> ClassificationResponse:
    """
    Classify the intent of a given text.
    
    Args:
        request: Classification request containing the text
        agent: Intent Agent instance (injected)
        options: Optional list of intent options to consider
        
    Returns:
        Classification response with intent and confidence
    """
    try:
        logger.info(f"Classifying intent for text: {request.text}")
        # Process classification using the agent's task engine
        result = await agent.process_query(request.text)
        
        # Format the response
        response = {
            "intent": result["intent"],
            "confidence": result["confidence"],
            "alternatives": []
        }
        
        return ClassificationResponse(**response)
    except Exception as e:
        logger.error(f"Error classifying intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

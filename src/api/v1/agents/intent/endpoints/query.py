"""Query processing endpoints for Intent Agent."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from src.api.v1.agents.intent.schemas import IntentRequest, IntentResponse
from src.api.v1.agents.intent.dependencies import get_intent_agent
from src.agents.intent_agent import IntentAgent
from src.routing.decision_maker import DecisionMaker

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize decision maker
decision_maker = DecisionMaker()

@router.post("/process", response_model=IntentResponse)
async def process_intent(
    request: IntentRequest,
    agent: IntentAgent = Depends(get_intent_agent)
) -> IntentResponse:
    """
    Process a query to determine intent and extract entities.

    Args:
        request: The intent processing request containing the query
        agent: Intent Agent instance (injected)

    Returns:
        Processed intent response
    """
    try:
        logger.info(f"[Intent Process] Received request: {request.query}")
        logger.debug(f"[Intent Process] Context: {request.context}")

        # Use decision maker to select the appropriate agent
        selected_agent = decision_maker.route_task("intent", context=request.context)
        if not selected_agent:
            logger.error("[Intent Process] No suitable agent found for intent processing")
            raise HTTPException(
                status_code=503,
                detail="No suitable agent available for processing"
            )

        logger.info(f"[Intent Process] Selected agent for processing: {selected_agent}")

        # Verify if the selected agent matches our instance
        if selected_agent != "intent_agent":
            logger.error(f"[Intent Process] Selected agent {selected_agent} does not match current agent")
            raise HTTPException(
                status_code=503,
                detail="Selected agent is not available"
            )

        # Process the query using the selected agent
        try:
            result = await agent.process_query(request.query)
            logger.info("[Intent Process] Query processed successfully")
            return IntentResponse(**result)
        except Exception as process_error:
            logger.error(f"[Intent Process] Error during query processing: {process_error}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing query: {str(process_error)}"
            )

    except HTTPException as http_error:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"[Intent Process] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
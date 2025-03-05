"""Dependencies for Intent Agent endpoints."""
from typing import Optional
from fastapi import Depends, HTTPException, Request
from src.agents.intent_agent import IntentAgent

async def get_intent_agent(request: Request) -> IntentAgent:
    """Get an instance of the Intent Agent from the application state."""
    tool_registry = request.app.state.tool_registry
    try:
        return IntentAgent(tool_registry=tool_registry)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize Intent Agent: {str(e)}"
        )

def validate_query_options(options: Optional[list] = None):
    """Validate classification options if provided."""
    async def _validate(request: Request):
        if options and not isinstance(options, list):
            raise HTTPException(
                status_code=400,
                detail="Invalid options format. Expected list of strings."
            )
        return options
    return _validate

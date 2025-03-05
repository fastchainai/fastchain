"""FastAPI endpoints for agent registry management."""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, List, Any
from pydantic import BaseModel

from src.agents.registry import AgentRegistry

router = APIRouter()

class AgentMetadata(BaseModel):
    """Pydantic model for agent metadata validation."""
    agent_name: str
    version: str
    capabilities: List[str]
    status: str
    configuration: Dict[str, Any]

@router.get("/", response_model=Dict[str, Any], tags=["Agent Registry"])
async def get_all_agents():
    """Retrieve all registered agents."""
    try:
        registry = AgentRegistry.get_instance()
        return registry.get_all_agents()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve agents: {str(e)}"
        )

@router.post("/register/", response_model=Dict[str, Any], tags=["Agent Registry"])
async def register_agent(metadata: AgentMetadata):
    """Register a new agent with the system."""
    try:
        registry = AgentRegistry.get_instance()
        registry.register_agent(metadata.agent_name, metadata.dict())
        return {
            "status": "success",
            "message": f"Agent {metadata.agent_name} registered successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register agent: {str(e)}"
        )

@router.get("/{agent_name}/", response_model=Dict[str, Any], tags=["Agent Registry"])
async def get_agent(agent_name: str):
    """Retrieve metadata for a specific agent."""
    try:
        registry = AgentRegistry.get_instance()
        agent = registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_name} not found"
            )
        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve agent: {str(e)}"
        )

@router.put("/{agent_name}/", response_model=Dict[str, Any], tags=["Agent Registry"])
async def update_agent(agent_name: str, metadata: AgentMetadata):
    """Update an existing agent's metadata."""
    try:
        registry = AgentRegistry.get_instance()
        registry.update_agent(agent_name, metadata.dict())
        return {
            "status": "success",
            "message": f"Agent {agent_name} updated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent: {str(e)}"
        )

@router.get("/capability/{capability}/", response_model=List[str], tags=["Agent Registry"])
async def get_agents_by_capability(capability: str):
    """Find agents with a specific capability."""
    try:
        registry = AgentRegistry.get_instance()
        return registry.get_agents_by_capability(capability)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve agents by capability: {str(e)}"
        )

@router.get("/active/", response_model=List[str], tags=["Agent Registry"])
async def get_active_agents():
    """Get a list of currently active agents."""
    try:
        registry = AgentRegistry.get_instance()
        return registry.get_active_agents()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active agents: {str(e)}"
        )

@router.delete("/{agent_name}/", response_model=Dict[str, Any], tags=["Agent Registry"])
async def unregister_agent(agent_name: str):
    """Unregister an agent from the system."""
    try:
        registry = AgentRegistry.get_instance()
        registry.unregister_agent(agent_name)
        return {
            "status": "success",
            "message": f"Agent {agent_name} unregistered successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unregister agent: {str(e)}"
        )
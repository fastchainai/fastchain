"""Intent Agent Manager for handling lifecycle and task delegation."""
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from src.agents.registry import AgentRegistry
from src.context.context_manager import ContextManager
from .agent import IntentAgent
from .utils import format_intent_response, validate_intent_request

logger = logging.getLogger(__name__)

class IntentAgentManager:
    """
    Manages the lifecycle of the Intent Agent, including startup, shutdown,
    task delegation, and context management.
    """
    def __init__(self, tool_registry: Optional[Any] = None):
        """Initialize the Intent Agent Manager."""
        logger.info("[Intent Agent] Initializing Intent Agent Manager")
        self.tool_registry = tool_registry
        self.agent = None
        self.context_manager = ContextManager()  # Initialize Context Manager
        self._initialize_agent()
        logger.info("[Intent Agent] Intent Agent Manager initialized successfully")

    def _initialize_agent(self):
        """Initialize and start the Intent Agent."""
        try:
            logger.info("[Intent Agent] Initializing Intent Agent")
            self.agent = IntentAgent(tool_registry=self.tool_registry)
            self.agent.update_status("active")
            logger.info("[Intent Agent] Intent Agent initialized successfully")
        except Exception as e:
            logger.error(f"[Intent Agent] Failed to initialize Intent Agent: {e}")
            raise

    def start(self):
        """Start the Intent Agent and mark it as active."""
        try:
            if not self.agent:
                self._initialize_agent()
            self.agent.update_status("active")
            logger.info("[Intent Agent] Intent Agent started successfully")
        except Exception as e:
            logger.error(f"[Intent Agent] Failed to start Intent Agent: {e}")
            raise

    def stop(self):
        """Stop the Intent Agent and mark it as inactive."""
        if self.agent:
            try:
                self.agent.update_status("inactive")
                logger.info("[Intent Agent] Intent Agent stopped successfully")
            except Exception as e:
                logger.error(f"[Intent Agent] Failed to stop Intent Agent: {e}")
                raise

    async def process_task(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a task using the Intent Agent and maintain context.

        Args:
            query: The input query to process
            session_id: Optional session ID for context continuity

        Returns:
            Dict containing the processing results
        """
        if not self.agent:
            raise RuntimeError("Intent Agent not initialized")

        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            self.context_manager.create_session(session_id)
            logger.info(f"[Intent Agent] Created new session: {session_id}")

        start_time = datetime.utcnow()
        try:
            # Store initial query in context
            self.context_manager.set_context(session_id, "current_query", {
                "text": query,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "user_input"
            })

            # Process the query
            result = await self.agent.process_query(query)

            # Update context with the processing result
            context_update = {
                "last_processed": {
                    "query": query,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "intent_history": {
                    "latest": result.get("intent", {}),
                    "entities": result.get("entities", {})
                }
            }
            self.context_manager.update_partial_context(session_id, context_update)

            # Calculate and update performance metrics
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.agent.update_metrics(response_time)

            return result

        except Exception as e:
            # Update metrics with error
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.agent.update_metrics(response_time, error=True)

            # Update context with error information
            error_context = {
                "last_error": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e),
                    "query": query
                }
            }
            self.context_manager.update_partial_context(session_id, error_context)

            logger.error(f"[Intent Agent] Error processing task: {e}")
            raise RuntimeError(f"Failed to process query: {str(e)}")

    def get_agent_status(self) -> Dict[str, Any]:
        """Get the current status of the Intent Agent."""
        if not self.agent:
            return {"status": "not_initialized"}
        return {
            "status": self.agent.metadata["status"],
            "last_updated": self.agent.metadata["last_updated"],
            "performance": self.agent.metadata["performance"]
        }

    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get the context for a specific session."""
        try:
            return self.context_manager.get_context(session_id)
        except Exception as e:
            logger.error(f"[Intent Agent] Error getting session context: {e}")
            return {}

    def clear_session_context(self, session_id: str) -> None:
        """Clear the context for a specific session."""
        try:
            self.context_manager.delete_context(session_id)
            logger.info(f"[Intent Agent] Cleared context for session: {session_id}")
        except Exception as e:
            logger.error(f"[Intent Agent] Error clearing session context: {e}")
            raise
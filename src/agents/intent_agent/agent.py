"""Intent Agent entry point."""
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from src.agents.registry import AgentRegistry
from src.utils.metrics import Metrics
from .task_engine import TaskEngine
from .utils import format_intent_response, validate_intent_request

logger = logging.getLogger(__name__)

class IntentAgent:
    """Intent Agent main class responsible for initializing the agent and managing its lifecycle."""

    def __init__(self, tool_registry: Optional[Any] = None):
        """Initialize the Intent Agent and register with the central registry."""
        logger.info("[Intent Agent] Initializing Intent Agent")
        self.tool_registry = tool_registry
        self.agent_dir = os.path.dirname(os.path.abspath(__file__))
        self.metadata = self._load_metadata()
        self.task_engine = TaskEngine()

        # Initialize metrics with service name and default tags
        self.metrics = Metrics(
            service_name="intent_agent",
            default_tags={
                "agent": "intent_agent",
                "version": self.metadata.get("version", "unknown")
            }
        )

        self._register_agent()
        logger.info("[Intent Agent] Intent Agent initialized successfully")

    def _load_metadata(self) -> Dict[str, Any]:
        """Load agent metadata from agent.json."""
        metadata_path = os.path.join(self.agent_dir, "agent.json")
        try:
            logger.debug(f"[Intent Agent] Loading metadata from {metadata_path}")
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            logger.debug(f"[Intent Agent] Loaded metadata: {metadata}")
            return metadata
        except Exception as e:
            logger.error(f"[Intent Agent] Failed to load agent metadata: {e}")
            raise RuntimeError(f"Failed to load agent metadata: {e}")

    def _register_agent(self):
        """Register the agent with the central registry."""
        try:
            logger.info("[Intent Agent] Registering agent with central registry")
            registry = AgentRegistry.get_instance()

            # Update last_updated timestamp
            self.metadata["last_updated"] = datetime.utcnow().isoformat() + "Z"
            self.metadata["status"] = "active"

            # Initialize performance metrics if not present
            self.metadata.setdefault("performance", {
                "response_time_ms": 0,
                "error_rate": 0.0,
                "request_count": 0
            })

            registry.register_agent("intent_agent", self.metadata)
            self.metrics.increment("agent.registrations")
            logger.info("[Intent Agent] Agent registered successfully")

        except ValueError:
            # Agent already registered, update instead
            logger.info("[Intent Agent] Agent already registered, updating metadata")
            registry = AgentRegistry.get_instance()
            registry.update_agent("intent_agent", self.metadata)
            self.metrics.increment("agent.updates")
            logger.info("[Intent Agent] Agent metadata updated successfully")

    def update_status(self, status: str):
        """Update agent status in the registry."""
        logger.info(f"[Intent Agent] Updating agent status to: {status}")
        self.metadata["status"] = status
        self.metadata["last_updated"] = datetime.utcnow().isoformat() + "Z"
        registry = AgentRegistry.get_instance()
        registry.update_agent("intent_agent", self.metadata)
        self.metrics.increment("agent.status_updates", tags={"status": status})
        logger.info("[Intent Agent] Agent status updated successfully")

    def update_metrics(self, response_time: float, error: bool = False):
        """Update performance metrics."""
        logger.debug(f"[Intent Agent] Updating metrics - response_time: {response_time}ms, error: {error}")

        # Update internal metadata
        if "performance" not in self.metadata:
            self.metadata["performance"] = {
                "response_time_ms": 0,
                "error_rate": 0.0,
                "request_count": 0
            }

        perf = self.metadata["performance"]
        perf["response_time_ms"] = response_time
        perf["request_count"] += 1

        if error:
            current_errors = perf["request_count"] * perf["error_rate"]
            new_total = current_errors + 1
            perf["error_rate"] = new_total / perf["request_count"]
            self.metrics.increment("agent.errors")

        # Record metrics
        self.metrics.gauge("agent.response_time", response_time)
        self.metrics.gauge("agent.error_rate", perf["error_rate"])
        self.metrics.increment("agent.requests")

        # Update registry
        registry = AgentRegistry.get_instance()
        try:
            registry.update_agent("intent_agent", {
                "performance": self.metadata["performance"],
                "last_updated": datetime.utcnow().isoformat() + "Z"
            })
            logger.debug("[Intent Agent] Metrics updated successfully")
        except Exception as e:
            logger.error(f"[Intent Agent] Failed to update metrics in registry: {e}")
            self.metrics.increment("agent.update_failures")

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query to determine intent using the task engine."""
        start_time = datetime.now()
        try:
            logger.info(f"[Intent Agent] Processing query: {query}")
            validate_intent_request(query)

            # Use metrics.time() for automatic timing
            result, processing_time = self.metrics.time(
                "agent.query_processing",
                lambda: self.task_engine.process_query(query)
            )

            # Format the response
            formatted_result = format_intent_response(result)
            logger.info("[Intent Agent] Query processed successfully")

            # Update metrics with success
            processing_time_ms = processing_time * 1000  # Convert to milliseconds
            self.update_metrics(processing_time_ms, error=False)

            return formatted_result

        except Exception as e:
            logger.error(f"[Intent Agent] Error processing query: {e}", exc_info=True)
            # Update metrics with error
            processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.update_metrics(processing_time_ms, error=True)
            raise RuntimeError(f"Failed to process query: {str(e)}")

    def get_context_status(self) -> Dict[str, Any]:
        """Get the current context status."""
        try:
            status = {
                "has_context": True,
                "last_updated": self.metadata["last_updated"],
                "interaction_count": self.metadata.get("performance", {}).get("request_count", 0)
            }
            self.metrics.gauge("agent.interaction_count", status["interaction_count"])
            return status
        except Exception as e:
            logger.error(f"[Intent Agent] Error getting context status: {e}")
            self.metrics.increment("agent.errors", tags={"type": "context_status"})
            raise RuntimeError(f"Failed to get context status: {str(e)}")

    def get_learning_status(self) -> Dict[str, Any]:
        """Get analytics about the learning process."""
        try:
            status = {
                "performance": self.metadata.get("performance", {}),
                "last_updated": self.metadata["last_updated"],
                "status": self.metadata["status"]
            }
            self.metrics.gauge("agent.learning.success_rate", 
                             1 - status["performance"].get("error_rate", 0))
            return status
        except Exception as e:
            logger.error(f"[Intent Agent] Error getting learning status: {e}")
            self.metrics.increment("agent.errors", tags={"type": "learning_status"})
            raise RuntimeError(f"Failed to get learning status: {str(e)}")
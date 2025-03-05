"""Agent Registry implementation for multi-agent system."""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.config import config

from src.utils.logging import Logging


# Initialize structured logging
logger = Logging(__name__)

class AgentRegistry:
    """
    A singleton class that manages agent metadata for the multi-agent system.
    Provides centralized registration and discovery of agents with their capabilities,
    status, and configuration.
    """
    _instance = None
    _file_path = "src/agents/registry.json"
    _settings = None

    def __init__(self):
        """Initialize the AgentRegistry singleton."""
        if AgentRegistry._instance is not None:
            raise Exception("AgentRegistry is a singleton. Use get_instance() instead.")

        # Initialize registry storage
        self._agents: Dict[str, Any] = {}
        self._load_from_file()

        # Set up metrics if enabled
        if config.settings.get('ENABLE_PROMETHEUS', False):
            self._setup_metrics()

        logger.info("Agent Registry initialized successfully")

    @classmethod
    def get_instance(cls) -> 'AgentRegistry':
        """Return the singleton instance of the AgentRegistry."""
        if cls._instance is None:
            cls._instance = AgentRegistry()
        return cls._instance

    def is_agent_registered(self, agent_name: str) -> bool:
        """
        Check if an agent is already registered.

        Args:
            agent_name: Name of the agent to check

        Returns:
            bool: True if the agent is registered, False otherwise
        """
        return agent_name in self._agents

    def _setup_metrics(self) -> None:
        """Set up Prometheus metrics for monitoring."""
        try:
            from prometheus_client import Counter, Gauge

            self._metrics = {
                'agent_registrations': Counter(
                    'agent_registrations_total',
                    'Total number of agent registrations'
                ),
                'active_agents': Gauge(
                    'active_agents',
                    'Number of currently active agents'
                )
            }
        except Exception as e:
            logger.error("Failed to setup metrics", error=str(e))

    def _load_from_file(self) -> None:
        """Load the agent metadata from the JSON file."""
        try:
            if os.path.exists(self._file_path):
                with open(self._file_path, "r") as file:
                    self._agents = json.load(file)
                logger.info("Loaded agent registry from file", 
                          agents_count=len(self._agents))
        except Exception as e:
            logger.error("Failed to load registry file", 
                        error=str(e),
                        file_path=self._file_path)
            self._agents = {}

    def _save_to_file(self) -> None:
        """Save the current state of the agent registry to the JSON file."""
        try:
            os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
            with open(self._file_path, "w") as file:
                json.dump(self._agents, file, indent=4)
            logger.info("Saved agent registry to file",
                       agents_count=len(self._agents))
        except Exception as e:
            logger.error("Failed to save registry file",
                        error=str(e),
                        file_path=self._file_path)

    def register_agent(self, agent_name: str, metadata: Dict[str, Any]) -> None:
        """
        Register a new agent with its metadata.

        Args:
            agent_name: Unique identifier for the agent
            metadata: Dictionary containing agent metadata including:
                     - capabilities: List of agent capabilities
                     - status: Current operational status
                     - version: Agent version
                     - configuration: Agent-specific config

        Raises:
            ValueError: If the agent is already registered
        """
        if self.is_agent_registered(agent_name):
            raise ValueError(f"Agent '{agent_name}' is already registered")

        # Add registration timestamp and initial status
        metadata.update({
            "registered_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "status": metadata.get("status", "initializing")
        })

        self._agents[agent_name] = metadata
        self._save_to_file()

        # Update metrics if enabled
        if hasattr(self, '_metrics'):
            self._metrics['agent_registrations'].inc()
            self._update_active_agents_metric()

        logger.info("Agent registered successfully",
                   agent_name=agent_name,
                   capabilities=metadata.get("capabilities", []))

    def update_agent(self, agent_name: str, metadata: Dict[str, Any]) -> None:
        """
        Update the metadata for an existing agent.

        Args:
            agent_name: Name of the agent to update
            metadata: Updated metadata dictionary

        Raises:
            ValueError: If the agent is not registered
        """
        if agent_name not in self._agents:
            raise ValueError(f"Agent '{agent_name}' is not registered")

        # Update only provided fields while preserving existing data
        self._agents[agent_name].update(metadata)
        self._agents[agent_name]["last_updated"] = datetime.utcnow().isoformat()

        self._save_to_file()

        # Update metrics if status changed
        if hasattr(self, '_metrics') and "status" in metadata:
            self._update_active_agents_metric()

        logger.info("Agent updated successfully",
                   agent_name=agent_name,
                   update_fields=list(metadata.keys()))

    def get_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for a specific agent.

        Args:
            agent_name: Name of the agent to retrieve

        Returns:
            Dict containing agent metadata if found, None otherwise
        """
        return self._agents.get(agent_name)

    def get_all_agents(self) -> Dict[str, Any]:
        """
        Return metadata for all registered agents.

        Returns:
            Dict containing all agent metadata
        """
        return self._agents.copy()

    def get_agents_by_capability(self, capability: str) -> List[str]:
        """
        Find agents that have a specific capability.

        Args:
            capability: The capability to search for

        Returns:
            List of agent names that have the specified capability
        """
        return [
            name for name, metadata in self._agents.items()
            if capability in metadata.get("capabilities", [])
        ]

    def get_active_agents(self) -> List[str]:
        """
        Get a list of currently active agents.

        Returns:
            List of names of active agents
        """
        return [
            name for name, metadata in self._agents.items()
            if metadata.get("status") == "active"
        ]

    def unregister_agent(self, agent_name: str) -> None:
        """
        Unregister an agent by removing its metadata.

        Args:
            agent_name: Name of the agent to unregister

        Raises:
            ValueError: If the agent is not registered
        """
        if agent_name not in self._agents:
            raise ValueError(f"Agent '{agent_name}' is not registered")

        del self._agents[agent_name]
        self._save_to_file()

        # Update metrics if enabled
        if hasattr(self, '_metrics'):
            self._update_active_agents_metric()

        logger.info("Agent unregistered successfully", agent_name=agent_name)

    def _update_active_agents_metric(self) -> None:
        """Update the active agents metric."""
        if hasattr(self, '_metrics'):
            active_count = len(self.get_active_agents())
            self._metrics['active_agents'].set(active_count)
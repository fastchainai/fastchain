"""
Base Agent Module

This module defines the foundational abstract base class for all agents in FastChain AI.
It provides core functionality, lifecycle management, and integration with system utilities.
"""
import os
import json

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path

from src.config import config

from src.utils.logging import Logging
from src.utils.metrics import Metrics
from src.utils.tracing import Tracing

from src.agents.registry import AgentRegistry


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the FastChain AI system.
    
    Provides core functionality and lifecycle management for derived agent implementations.
    """
    
    def __init__(self, agent_name: str) -> None:
        """
        Initialize the base agent with required components and configuration.
        
        Args:
            agent_id (str): Unique identifier for the agent instance
        """
        self.name = agent_name
        self.logger = Logging(self.name)
        self.metrics = Metrics(self.name)
        self.tracer = Tracing(self.name)
        
        # Load agent configuration
        self.config = self._load_agent_config()
        
        # Initialize agent registry
        self.registry = AgentRegistry()
        
        # Register agent
        self._register_agent()
        
        self.logger.info(
            "Agent initialized",
            agent_name=self.name,
            config=self.config
        )

    def _load_agent_config(self) -> Dict[str, Any]:
        """
        Load agent configuration from agent.json and merge with global settings.
        
        Returns:
            Dict[str, Any]: Merged configuration dictionary
        """
        # Get agent class directory path
        agent_dir = Path(os.path.dirname(self.__class__.__module__.replace('.', '/')))
        config_path = agent_dir / 'agent.json'
        
        try:
            with open(config_path) as f:
                agent_config = json.load(f)
        except FileNotFoundError:
            self.logger.warning(
                "Agent config file not found",
                config_path=str(config_path)
            )
            agent_config = {}
            
        # Merge with global config
        merged_config = {
            **config.as_dict(),
            **agent_config
        }
        
        return merged_config

    def _register_agent(self) -> None:
        """Register the agent with the central registry."""
        try:
            self.registry.register_agent(
                self.agent_id,
                {
                    "status": "initialized",
                    "type": self.__class__.__name__,
                    "capabilities": self.config.get("capabilities", []),
                }
            )
        except Exception as e:
            self.logger.error(
                "Failed to register agent",
                error=str(e),
                agent_id=self.agent_id
            )
            raise

    async def initialize(self) -> None:
        """
        Initialize agent resources and start monitoring.
        
        This method should be called before the agent begins processing.
        """
        with self.tracer.start_as_current_span("agent_initialize") as span:
            span.set_attribute("agent.id", self.agent_id)
            
            try:
                await self._initialize_resources()
                self.metrics.record_initialization()
                
                self.logger.info(
                    "Agent resources initialized",
                    agent_id=self.agent_id
                )
            except Exception as e:
                self.logger.error(
                    "Failed to initialize agent resources",
                    error=str(e),
                    agent_id=self.agent_id
                )
                raise

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the agent and cleanup resources.
        
        This method should be called when the agent is being terminated.
        """
        with self.tracer.start_as_current_span("agent_shutdown") as span:
            span.set_attribute("agent.id", self.agent_id)
            
            try:
                await self._cleanup_resources()
                self.metrics.record_shutdown()
                
                self.logger.info(
                    "Agent shutdown complete",
                    agent_id=self.agent_id
                )
            except Exception as e:
                self.logger.error(
                    "Error during agent shutdown",
                    error=str(e),
                    agent_id=self.agent_id
                )
                raise

    @abstractmethod
    async def run(self, input_data: Any) -> Any:
        """
        Process input data and return results.
        
        This method must be implemented by derived agent classes.
        
        Args:
            input_data: Input data to be processed by the agent
            
        Returns:
            Processing results in the format specified by the derived agent
        """
        raise NotImplementedError("Derived agents must implement run()")

    @abstractmethod
    async def _initialize_resources(self) -> None:
        """
        Initialize agent-specific resources.
        
        This method must be implemented by derived agent classes.
        """
        raise NotImplementedError("Derived agents must implement _initialize_resources()")

    @abstractmethod
    async def _cleanup_resources(self) -> None:
        """
        Cleanup agent-specific resources.
        
        This method must be implemented by derived agent classes.
        """
        raise NotImplementedError("Derived agents must implement _cleanup_resources()")

    def __repr__(self) -> str:
        """Return string representation of the agent."""
        return f"{self.__class__.__name__}(agent_id='{self.agent_id}')"

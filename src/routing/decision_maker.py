"""Decision Making Module

This module is responsible for dynamically routing tasks to the most suitable agent based on capabilities, performance metrics, and current load.
"""
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone

from src.agents.registry import AgentRegistry

logger = logging.getLogger(__name__)

class DecisionMaker:
    """
    Decision Making Module that handles intelligent task routing in the multi-agent system.
    """

    def __init__(self):
        """Initialize the Decision Maker with default configuration."""
        self.registry = AgentRegistry.get_instance()
        self.weight_performance = 0.6  # Performance weight in scoring
        self.weight_load = 0.4        # Load weight in scoring
        logger.info("Decision Maker initialized with weights: performance=%.2f, load=%.2f",
                   self.weight_performance, self.weight_load)

    def get_load_metrics(self) -> Dict[str, float]:
        """
        Get current load metrics for each agent from the registry.

        Returns:
            Dict[str, float]: Agent load metrics (0.0 to 1.0, where 1.0 is fully loaded)
        """
        agents_data = self.registry.get_all_agents()
        load_metrics = {}

        for agent_id, metadata in agents_data.items():
            try:
                # Get direct load if available, otherwise calculate from performance metrics
                if "load" in metadata:
                    load_metrics[agent_id] = float(metadata["load"])
                else:
                    # Calculate load based on recent request count and response times
                    performance = metadata.get("performance", {})
                    recent_requests = performance.get("request_count", 0)
                    avg_response_time = performance.get("response_time_ms", 100)

                    # Normalize load metric between 0 and 1
                    load = min(1.0, (recent_requests * avg_response_time) / 10000)
                    load_metrics[agent_id] = load

                logger.debug("Load metric for %s: %.2f", agent_id, load_metrics[agent_id])
            except Exception as e:
                logger.warning("Failed to calculate load for agent %s: %s", agent_id, e)
                raise RuntimeError(f"Invalid metrics for agent {agent_id}: {str(e)}")

        return load_metrics

    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Get performance metrics for each agent from the registry.

        Returns:
            Dict[str, float]: Agent performance scores (0.0 to 1.0)
        """
        agents_data = self.registry.get_all_agents()
        performance_metrics = {}

        for agent_id, metadata in agents_data.items():
            try:
                # Handle both dict and direct float formats for performance
                performance = metadata.get("performance", {})
                if isinstance(performance, dict):
                    if "success_rate" not in performance:
                        raise RuntimeError("Missing success_rate in performance metrics")
                    success_rate = float(performance.get("success_rate", 0.0))
                else:
                    success_rate = float(performance) if performance is not None else 0.0
                performance_metrics[agent_id] = success_rate

                logger.debug("Performance metric for %s: %.2f", agent_id, performance_metrics[agent_id])
            except Exception as e:
                logger.warning("Failed to calculate performance for agent %s: %s", agent_id, e)
                raise RuntimeError(f"Invalid metrics for agent {agent_id}: {str(e)}")

        return performance_metrics

    def get_candidate_agents(self, required_capability: str) -> List[str]:
        """
        Get a list of agents that have the required capability.

        Args:
            required_capability: The capability required for the task

        Returns:
            List[str]: List of qualifying agent IDs
        """
        agents_data = self.registry.get_all_agents()
        all_candidates = []
        active_candidates = []

        for agent_id, metadata in agents_data.items():
            if required_capability in metadata.get("capabilities", []):
                all_candidates.append(agent_id)
                if metadata.get("status") == "active":
                    active_candidates.append(agent_id)

        if not all_candidates:
            raise RuntimeError(f"No agents found with capability: {required_capability}")
        if not active_candidates:
            raise RuntimeError(f"No active agents found with capability: {required_capability}")

        return active_candidates

    def calculate_agent_score(self, agent_id: str, 
                            load_metrics: Dict[str, float],
                            performance_metrics: Dict[str, float]) -> float:
        """
        Calculate a score for an agent based on its performance and load metrics.

        Args:
            agent_id: The agent to score
            load_metrics: Dictionary of agent load metrics
            performance_metrics: Dictionary of agent performance metrics

        Returns:
            float: The calculated score (higher is better)
        """
        # Get metrics
        load = float(load_metrics.get(agent_id, 1.0))
        performance = float(performance_metrics.get(agent_id, 0.5))

        # Calculate weighted score (higher performance and lower load is better)
        score = (self.weight_performance * performance) + (self.weight_load * (1 - load))

        logger.debug("Score for agent %s: %.2f (perf=%.2f, load=%.2f)",
                    agent_id, score, performance, load)
        return score

    def route_task(self, required_capability: str, 
                  context: Optional[Dict[str, Any]] = None) -> str:
        """Route a task to the best-suited agent based on capability, performance, and load."""
        try:
            logger.info(f"[Decision Maker] Starting task routing for capability: {required_capability}")

            # Get candidate agents - this will raise appropriate errors if no agents are found
            candidates = self.get_candidate_agents(required_capability)

            # Get metrics
            try:
                load_metrics = self.get_load_metrics()
                performance_metrics = self.get_performance_metrics()
            except RuntimeError as e:
                logger.error(f"[Decision Maker] Failed to get metrics: {e}")
                raise

            # Check for missing metrics
            for agent_id in candidates:
                if agent_id not in load_metrics or agent_id not in performance_metrics:
                    error_msg = f"Invalid metrics for agent: {agent_id}"
                    logger.error(f"[Decision Maker] {error_msg}")
                    raise RuntimeError(error_msg)

            # Calculate scores for each candidate
            candidate_scores = {
                agent_id: self.calculate_agent_score(
                    agent_id, load_metrics, performance_metrics
                )
                for agent_id in candidates
            }

            selected_agent = max(candidate_scores.items(), key=lambda x: x[1])[0]
            logger.info(f"[Decision Maker] Selected agent {selected_agent} for capability {required_capability} "
                       f"(score: {candidate_scores[selected_agent]:.2f})")

            # Update selected agent's metadata in registry
            self.registry.update_agent(selected_agent, {
                "last_selected": datetime.now(timezone.utc).isoformat(),
                "current_task": required_capability
            })

            return selected_agent

        except Exception as e:
            logger.error(f"[Decision Maker] Error routing task: {e}", exc_info=True)
            raise
"""Dynamic Workflow Orchestrator for Intent Agent System.

This module builds and maintains a directed graph representing the multi-agent system's
workflow, automatically syncing with the Agent Registry and updating based on real-time events.
"""
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime

import networkx as nx
import matplotlib.pyplot as plt

from src.agents.registry import AgentRegistry
from src.utils.logging import Logging
from src.utils.metrics import Metrics
from src.utils.tracing import SpanContextManager

# Initialize logger with the new centralized logging system
logger = Logging(__name__)

# Initialize metrics
metrics = Metrics(
    service_name="workflow_orchestrator",
    default_tags={"component": "orchestration"}
)

class WorkflowOrchestrator:
    """
    The WorkflowOrchestrator maintains a dynamic graph representation of the multi-agent system.
    It automatically synchronizes with the Agent Registry and updates based on real-time events.
    """

    def __init__(self):
        """Initialize the workflow orchestrator with an empty graph."""
        with SpanContextManager("workflow_orchestrator_init") as span:
            try:
                logger.info("Initializing workflow orchestrator")
                self.graph = nx.DiGraph()
                self.registry = AgentRegistry.get_instance()
                self.last_sync = None
                self._register_event_handlers()

                metrics.increment("orchestrator.initialized")
                logger.info("Workflow orchestrator initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize WorkflowOrchestrator: {e}", exc_info=True)
                metrics.increment("orchestrator.initialization_errors")
                raise

    def _register_event_handlers(self):
        """Set up event handlers for real-time graph updates."""
        # TODO: Implement event handlers for real-time updates
        metrics.increment("orchestrator.event_handlers.registered")
        pass

    def sync_with_registry(self) -> None:
        """
        Synchronize the workflow graph with the current state of the Agent Registry.
        This includes adding nodes for active agents and creating edges based on metadata.
        """
        with SpanContextManager("sync_with_registry") as span:
            try:
                logger.info("Starting registry synchronization")
                metrics.increment("orchestrator.sync.started")

                # Clear existing graph for a fresh rebuild
                self.graph.clear()

                # Retrieve all agents from the registry
                all_agents = self.registry.get_all_agents()
                logger.debug(f"Retrieved {len(all_agents)} agents from registry")

                # Step 1: Add nodes for each active agent
                active_agents = 0
                for agent_id, metadata in all_agents.items():
                    if metadata.get("status") == "active":
                        self.graph.add_node(
                            agent_id,
                            **{
                                "status": "active",
                                "capabilities": metadata.get("capabilities", []),
                                "performance": metadata.get("performance", {}),
                                "last_updated": metadata.get("last_updated")
                            }
                        )
                        active_agents += 1
                        logger.debug(f"Added node for agent: {agent_id}")

                metrics.gauge("orchestrator.active_agents", active_agents)

                # Step 2: Build edges based on agent relationships and task flows
                edge_count = 0
                for agent_id, metadata in all_agents.items():
                    if not self.graph.has_node(agent_id):
                        continue

                    capabilities = metadata.get("capabilities", [])
                    for capability in capabilities:
                        for other_id, other_meta in all_agents.items():
                            if (other_id != agent_id and 
                                self.graph.has_node(other_id) and
                                capability in other_meta.get("capabilities", [])):

                                # Add edge with relevant metadata
                                self.graph.add_edge(
                                    agent_id,
                                    other_id,
                                    capability=capability,
                                    last_interaction=None,
                                    interaction_count=0
                                )
                                edge_count += 1
                                logger.debug(
                                    f"Added edge: {agent_id} -> {other_id} "
                                    f"(capability: {capability})"
                                )

                metrics.gauge("orchestrator.edge_count", edge_count)
                self.last_sync = datetime.now()

                logger.info(
                    f"Sync completed successfully. "
                    f"Graph has {self.graph.number_of_nodes()} nodes and "
                    f"{self.graph.number_of_edges()} edges"
                )
                metrics.increment("orchestrator.sync.completed")

                if span:
                    span.set_attributes({
                        "active_agents": active_agents,
                        "edge_count": edge_count
                    })

            except Exception as e:
                logger.error(f"Error during registry sync: {e}", exc_info=True)
                metrics.increment("orchestrator.sync.errors")
                if span:
                    span.record_exception(e)
                raise RuntimeError(f"Failed to sync with registry: {str(e)}")

    def add_custom_edge(self, 
                       source: str, 
                       destination: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Manually add an edge for runtime-discovered tasks or relationships.

        Args:
            source: The originating agent name
            destination: The target agent name
            metadata: Optional edge metadata (e.g., task info, timestamps)
        """
        try:
            if not self.graph.has_node(source):
                logger.warning(f"[WorkflowOrchestrator] Source node {source} not found, adding it")
                self.graph.add_node(source)

            if not self.graph.has_node(destination):
                logger.warning(f"[WorkflowOrchestrator] Destination node {destination} not found, adding it")
                self.graph.add_node(destination)

            edge_data = {
                "added_at": datetime.now().isoformat(),
                "last_interaction": None,
                "interaction_count": 0
            }
            if metadata:
                edge_data.update(metadata)

            self.graph.add_edge(source, destination, **edge_data)
            logger.info(f"[WorkflowOrchestrator] Added custom edge: {source} -> {destination}")

        except Exception as e:
            logger.error(f"[WorkflowOrchestrator] Error adding custom edge: {e}", exc_info=True)
            raise RuntimeError(f"Failed to add custom edge: {str(e)}")

    def update_workflow_with_events(self, events: List[Tuple[str, str, Dict[str, Any]]]) -> None:
        """
        Update the graph based on a list of workflow events.

        Args:
            events: List of (source_agent, target_agent, event_data) tuples
        """
        try:
            logger.info(f"[WorkflowOrchestrator] Processing {len(events)} workflow events")

            for source, destination, event_data in events:
                # Ensure both nodes exist
                for node in (source, destination):
                    if not self.graph.has_node(node):
                        logger.warning(f"[WorkflowOrchestrator] Node {node} not found, adding it")
                        self.graph.add_node(node)

                # Update or add edge with event data
                if self.graph.has_edge(source, destination):
                    # Update existing edge
                    edge_data = self.graph[source][destination]
                    edge_data["last_interaction"] = datetime.now().isoformat()
                    edge_data["interaction_count"] = edge_data.get("interaction_count", 0) + 1
                    edge_data.update(event_data)
                else:
                    # Add new edge
                    self.graph.add_edge(
                        source,
                        destination,
                        last_interaction=datetime.now().isoformat(),
                        interaction_count=1,
                        **event_data
                    )

                logger.debug(
                    f"[WorkflowOrchestrator] Updated edge: {source} -> {destination} "
                    f"with event data"
                )

            logger.info("[WorkflowOrchestrator] Workflow events processed successfully")

        except Exception as e:
            logger.error(f"[WorkflowOrchestrator] Error processing workflow events: {e}", exc_info=True)
            raise RuntimeError(f"Failed to process workflow events: {str(e)}")

    def get_node_data(self, node_id: str) -> Dict[str, Any]:
        """
        Get detailed data for a specific node, including registry metadata.

        Args:
            node_id: The ID of the node to query

        Returns:
            Dict containing node data and related registry metadata
        """
        try:
            if not self.graph.has_node(node_id):
                raise ValueError(f"Node {node_id} not found in graph")

            # Get basic node data from graph
            node_data = dict(self.graph.nodes[node_id])

            # Enrich with registry metadata
            registry_data = self.registry.get_agent(node_id)
            if registry_data:
                node_data.update({
                    "status": registry_data.get("status"),
                    "capabilities": registry_data.get("capabilities", []),
                    "performance": registry_data.get("performance", {}),
                    "last_updated": registry_data.get("last_updated")
                })

            return node_data

        except Exception as e:
            logger.error(f"[WorkflowOrchestrator] Error getting node data: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get node data: {str(e)}")

    def get_edge_history(self, source: str, destination: str) -> List[Dict[str, Any]]:
        """
        Get interaction history for an edge between two agents.

        Args:
            source: Source agent ID
            destination: Destination agent ID

        Returns:
            List of historical interactions
        """
        try:
            if not self.graph.has_edge(source, destination):
                return []

            edge_data = self.graph[source][destination]
            return edge_data.get("history", [])

        except Exception as e:
            logger.error(f"[WorkflowOrchestrator] Error getting edge history: {e}", exc_info=True)
            return []

    def visualize(self, title: str = "Dynamic Workflow Orchestrator") -> None:
        """
        Visualize the current state of the workflow graph.
        """
        pos = nx.spring_layout(self.graph)  # Layout for nodes
        edge_labels = nx.get_edge_attributes(self.graph, 'task')

        nx.draw(self.graph, pos, with_labels=True, node_color="skyblue", node_size=2000, arrows=True)
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels)

        plt.title(title)
        plt.show()


if __name__ == "__main__":
    # Example usage and testing
    orchestrator = WorkflowOrchestrator()

    # Sync with registry to build initial graph
    orchestrator.sync_with_registry()

    # Example: Process some workflow events
    test_events = [
        ("intent_agent", "chat_agent", {"task": "process_query", "priority": "high"}),
        ("chat_agent", "reasoning_agent", {"task": "analyze_response", "priority": "medium"})
    ]
    orchestrator.update_workflow_with_events(test_events)

    orchestrator.visualize()
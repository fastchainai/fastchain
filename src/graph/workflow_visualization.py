"""Dynamic Workflow Visualization for Intent Agent System.

This module provides real-time visualization of the multi-agent system's workflow graph,
incorporating live metrics and performance data from the Agent Registry.
"""
from typing import Dict, Any, Optional, Tuple
import os
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
    service_name="workflow_visualizer",
    default_tags={"component": "visualization"}
)

class WorkflowVisualizer:
    """Provides dynamic visualization of the multi-agent system's workflow graph."""

    def __init__(self, output_dir: str = "visualizations"):
        """Initialize the workflow visualizer.

        Args:
            output_dir: Directory to save visualization files
        """
        with SpanContextManager("workflow_visualizer_init") as span:
            try:
                self.registry = AgentRegistry.get_instance()
                self.output_dir = output_dir

                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    logger.info(f"Created visualization output directory: {output_dir}")
                    metrics.increment("visualizer.directory.created")

                self.node_colors = {
                    "active": "#90EE90",    # Light green
                    "inactive": "#D3D3D3",  # Light gray
                    "error": "#FFB6C1",     # Light red
                    "busy": "#FFD700"       # Gold
                }
                self.edge_colors = {
                    "high_traffic": "#FF4500",  # Orange Red
                    "normal": "#4682B4",        # Steel Blue
                    "low_traffic": "#A9A9A9"    # Dark Gray
                }

                metrics.increment("visualizer.initialized")
                logger.info("WorkflowVisualizer initialized successfully")

                if span:
                    span.set_attribute("output_dir", output_dir)

            except Exception as e:
                logger.error(f"Failed to initialize WorkflowVisualizer: {e}", exc_info=True)
                metrics.increment("visualizer.initialization_errors")
                raise

    def _get_node_color(self, metadata: Dict[str, Any]) -> str:
        """Determine node color based on agent status and metrics."""
        with SpanContextManager("get_node_color") as span:
            try:
                status = metadata.get("status", "unknown")
                if status == "active":
                    performance = metadata.get("performance", {})
                    load = performance.get("load", 0)
                    error_rate = performance.get("error_rate", 0)

                    if error_rate > 0.3:
                        metrics.increment("visualizer.nodes.error_state")
                        return self.node_colors["error"]
                    elif load > 0.8:
                        metrics.increment("visualizer.nodes.busy_state")
                        return self.node_colors["busy"]

                    metrics.increment("visualizer.nodes.active_state")
                    return self.node_colors["active"]

                metrics.increment("visualizer.nodes.inactive_state")
                return self.node_colors["inactive"]

            except Exception as e:
                logger.error(f"Error determining node color: {e}")
                metrics.increment("visualizer.color_determination_errors")
                return self.node_colors["error"]

    def visualize_workflow(self,
                         graph: nx.DiGraph,
                         title: str = "Multi-Agent System Workflow",
                         include_metrics: bool = True,
                         node_size_scale: float = 1.0,
                         save_to_file: bool = True) -> Optional[str]:
        """Create a visualization of the workflow graph with current metrics and status."""
        with SpanContextManager("visualize_workflow") as span:
            try:
                logger.info("Creating workflow visualization")
                metrics.increment("visualizer.graph_creation_attempts")

                plt.figure(figsize=(12, 8))
                pos = nx.spring_layout(graph, k=1, iterations=50)

                # Process nodes
                node_colors = []
                node_sizes = []
                node_labels = {}

                for node in graph.nodes():
                    metadata = self.registry.get_agent(node) or {}
                    node_colors.append(self._get_node_color(metadata))
                    size = self._calculate_node_size(metadata) * node_size_scale
                    node_sizes.append(size)
                    node_labels[node] = self._format_node_label(node, metadata, include_metrics)

                # Draw nodes
                nx.draw_networkx_nodes(
                    graph, pos,
                    node_color=node_colors,
                    node_size=node_sizes,
                    alpha=0.7
                )

                # Process edges
                edge_colors = []
                edge_labels = {}

                for u, v, data in graph.edges(data=True):
                    edge_colors.append(self._get_edge_color(data))
                    edge_labels[(u, v)] = self._format_edge_label(data)

                # Draw edges
                nx.draw_networkx_edges(
                    graph, pos,
                    edge_color=edge_colors,
                    arrows=True,
                    arrowsize=20,
                    width=2,
                    alpha=0.6
                )

                # Add labels
                nx.draw_networkx_labels(graph, pos, labels=node_labels, font_size=8)
                nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=7)

                plt.title(title)
                plt.axis('off')

                # Add timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                plt.figtext(0.02, 0.02, f'Updated: {timestamp}', fontsize=8)

                if save_to_file:
                    filename = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    filepath = os.path.join(self.output_dir, filename)
                    plt.savefig(filepath, dpi=300, bbox_inches='tight')
                    plt.close()

                    logger.info(f"Visualization saved to: {filepath}")
                    metrics.increment("visualizer.graphs_saved")

                    if span:
                        span.set_attribute("output_file", filepath)

                    return filepath
                else:
                    plt.show()
                    plt.close()
                    metrics.increment("visualizer.graphs_displayed")
                    return None

            except Exception as e:
                logger.error(f"Error creating visualization: {e}", exc_info=True)
                metrics.increment("visualizer.graph_creation_errors")
                if span:
                    span.record_exception(e)
                raise RuntimeError(f"Failed to create workflow visualization: {str(e)}")

    def _get_edge_color(self, edge_data: Dict[str, Any]) -> str:
        """Determine edge color based on interaction frequency and performance."""
        interaction_count = edge_data.get("interaction_count", 0)
        if interaction_count > 100:
            return self.edge_colors["high_traffic"]
        elif interaction_count > 10:
            return self.edge_colors["normal"]
        return self.edge_colors["low_traffic"]

    def _format_node_label(self, 
                          agent_id: str, 
                          metadata: Dict[str, Any],
                          include_metrics: bool = True) -> str:
        """Format node label with agent information and optional metrics."""
        label = f"{agent_id}\n"

        if include_metrics and "performance" in metadata:
            perf = metadata["performance"]
            label += f"Load: {perf.get('load', 0):.2f}\n"
            label += f"Success: {(1 - perf.get('error_rate', 0)):.2%}\n"
            label += f"Reqs: {perf.get('request_count', 0)}"

        return label

    def _format_edge_label(self, edge_data: Dict[str, Any]) -> str:
        """Format edge label with interaction information."""
        label = ""
        if "capability" in edge_data:
            label += f"{edge_data['capability']}\n"
        if "interaction_count" in edge_data:
            label += f"Count: {edge_data['interaction_count']}"
        return label

    def _calculate_node_size(self, metadata: Dict[str, Any]) -> float:
        """Calculate node size based on agent metrics."""
        base_size = 2000
        if "performance" in metadata:
            request_count = metadata["performance"].get("request_count", 0)
            # Increase size based on activity level
            size_factor = min(3, 1 + (request_count / 1000))
            return base_size * size_factor
        return base_size

    def create_metric_summary(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Generate a summary of current system metrics from the workflow graph."""
        with SpanContextManager("create_metric_summary") as span:
            try:
                summary = {
                    "total_agents": graph.number_of_nodes(),
                    "total_interactions": graph.number_of_edges(),
                    "active_agents": 0,
                    "total_requests": 0,
                    "avg_success_rate": 0.0,
                    "avg_load": 0.0,
                    "timestamp": datetime.now().isoformat()
                }

                success_rates = []
                loads = []

                for node in graph.nodes():
                    metadata = self.registry.get_agent(node) or {}
                    if metadata.get("status") == "active":
                        summary["active_agents"] += 1

                        if "performance" in metadata:
                            perf = metadata["performance"]
                            summary["total_requests"] += perf.get("request_count", 0)
                            success_rates.append(1 - perf.get("error_rate", 0))
                            loads.append(perf.get("load", 0))

                if success_rates:
                    summary["avg_success_rate"] = sum(success_rates) / len(success_rates)
                if loads:
                    summary["avg_load"] = sum(loads) / len(loads)

                # Record metrics
                metrics.gauge("system.total_agents", summary["total_agents"])
                metrics.gauge("system.active_agents", summary["active_agents"])
                metrics.gauge("system.total_requests", summary["total_requests"])
                metrics.gauge("system.avg_success_rate", summary["avg_success_rate"])
                metrics.gauge("system.avg_load", summary["avg_load"])

                if span:
                    span.set_attributes({
                        "total_agents": summary["total_agents"],
                        "active_agents": summary["active_agents"]
                    })

                return summary

            except Exception as e:
                logger.error(f"Error creating metric summary: {e}", exc_info=True)
                metrics.increment("visualizer.summary_creation_errors")
                if span:
                    span.record_exception(e)
                return {}

if __name__ == "__main__":
    from src.graph.workflow_orchestrator import WorkflowOrchestrator

    orchestrator = WorkflowOrchestrator()
    visualizer = WorkflowVisualizer()

    try:
        orchestrator.sync_with_registry()
        filepath = visualizer.visualize_workflow(orchestrator.graph, save_to_file=True)

        if filepath:
            print(f"\nVisualization saved to: {filepath}")

        summary = visualizer.create_metric_summary(orchestrator.graph)
        print("\nSystem Metrics Summary:")
        for key, value in summary.items():
            print(f"{key}: {value}")

    except Exception as e:
        logger.error(f"Error in main workflow visualization: {e}", exc_info=True)
        metrics.increment("visualizer.main_execution_errors")
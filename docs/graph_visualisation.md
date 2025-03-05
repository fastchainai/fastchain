# Graph Workflow Visualization

The Graph Workflow Visualization component provides an interactive, real-time visual representation of task flows and agent interactions within the multi-agent system. It builds on the dynamic graph created by the Workflow Orchestrator and enhances it by applying custom styling, labels, and metric annotations—all driven by live data from the Agent Registry.

---

## Table of Contents

- [Graph Workflow Visualization](#graph-workflow-visualization)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Architecture](#architecture)
    - [Key Components](#key-components)
  - [Implementation Details](#implementation-details)
    - [Dynamic Labels and Styling](#dynamic-labels-and-styling)
    - [Metric Integration](#metric-integration)
  - [Integration with Other Modules](#integration-with-other-modules)
    - [Agent Registry \& Decision-Making Module](#agent-registry--decision-making-module)
    - [Agent Managers](#agent-managers)
  - [Usage and Configuration](#usage-and-configuration)
    - [Running the Visualization](#running-the-visualization)
    - [Customization Options](#customization-options)
  - [Use Cases](#use-cases)
  - [Troubleshooting](#troubleshooting)
  - [Future Enhancements](#future-enhancements)

---

## Overview

The Graph Workflow Visualization component transforms the dynamic state of the multi-agent system into a graphical representation where each node represents an agent and each edge indicates task flow or interaction. This visualization aids in:

- **Monitoring:** Real-time display of routing decisions and agent interactions.
- **Debugging:** Quickly identifying misrouted tasks, performance bottlenecks, and communication issues.
- **Performance Analysis:** Visualizing load, response times, and other metrics to optimize agent operations.
- **Auditing:** Reviewing historical data to understand system behavior over time.

---

## Architecture

The visualization system is built using standard Python libraries:

- **Graph Construction:**  
  Relies on the directed graph maintained by the Workflow Orchestrator.
  
- **Data Ingestion:**  
  Pulls live metadata from the Agent Registry to dynamically update node labels and styling.
  
- **Rendering Engine:**  
  Uses NetworkX for graph manipulation and Matplotlib for rendering the final visual output.

### Key Components

- **Dynamic Labeling:**  
  Node labels are enriched with live metadata (e.g., load, performance) from the Agent Registry.
  
- **Custom Styling:**  
  Nodes and edges are styled based on agent status and metrics, with customizable colors and sizes.
  
- **Metric Integration:**  
  Optionally merges external metrics with registry data to provide a comprehensive view of agent performance.

---

## Implementation Details

The implementation is provided in `src/graph/workflow_visualisation.py` and includes the following features:

### Dynamic Labels and Styling

- **Live Data:**  
  The visualization queries the Agent Registry to automatically generate labels that include agent names and additional metrics (e.g., `load`, `performance`).
  
- **Color Coding:**  
  Active agents are highlighted (e.g., in light green) while others use default colors.

### Metric Integration

- **Combined Metrics:**  
  Optionally, external metrics can be merged with registry data to provide enhanced node labels showing detailed performance information.

Below is an example implementation:

```python
# src/graph/workflow_visualisation.py

import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, Any
from src.agents.registry import AgentRegistry

def visualize_with_registry_data(
    graph: nx.DiGraph,
    title: str = "Registry-Based Visualization"
) -> None:
    """
    Render the workflow graph using live data from the Agent Registry for dynamic labels and colors.
    
    Args:
        graph (nx.DiGraph): The workflow graph maintained by the orchestrator.
        title (str): Title for the visualization.
    """
    registry = AgentRegistry.get_instance()
    all_agents = registry.get_all_agents()

    labels = {}
    node_colors = []
    default_color = "skyblue"

    for node in graph.nodes():
        agent_metadata = all_agents.get(node, {})
        label = node

        # Enrich label with metrics if available
        load_value = agent_metadata.get("load")
        performance_value = agent_metadata.get("performance")
        if load_value is not None or performance_value is not None:
            label += "\n("
            if load_value is not None:
                label += f"load={load_value}"
            if performance_value is not None:
                if load_value is not None:
                    label += ", "
                label += f"perf={performance_value}"
            label += ")"

        labels[node] = label

        status = agent_metadata.get("status", "unknown")
        node_colors.append("lightgreen" if status == "active" else default_color)

    pos = nx.spring_layout(graph)
    edge_labels = nx.get_edge_attributes(graph, 'task')

    nx.draw(graph, pos, node_color=node_colors, with_labels=True, node_size=2000, arrows=True)
    nx.draw_networkx_labels(graph, pos, labels=labels)
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)

    plt.title(title)
    plt.show()

def visualize_metric_graph(
    graph: nx.DiGraph,
    external_metrics: Dict[str, Dict[str, Any]],
    title: str = "Metric-Enriched Visualization"
) -> None:
    """
    Render the workflow graph with additional external metrics merged with registry data.
    
    Args:
        graph (nx.DiGraph): The workflow graph.
        external_metrics (Dict[str, Dict[str, Any]]): External metrics keyed by agent name.
        title (str): Title for the visualization.
    """
    registry = AgentRegistry.get_instance()
    all_agents = registry.get_all_agents()

    labels = {}
    node_colors = []
    default_color = "skyblue"

    for node in graph.nodes():
        label = node
        registry_metadata = all_agents.get(node, {})
        agent_metrics = external_metrics.get(node, {})

        if registry_metadata or agent_metrics:
            label += "\n("
            reg_load = registry_metadata.get("load")
            reg_perf = registry_metadata.get("performance")
            ext_load = agent_metrics.get("load", reg_load)
            ext_perf = agent_metrics.get("performance", reg_perf)

            if ext_load is not None:
                label += f"load={ext_load}"
            if ext_perf is not None:
                if ext_load is not None:
                    label += ", "
                label += f"perf={ext_perf}"
            label += ")"

        labels[node] = label
        status = registry_metadata.get("status", "unknown")
        node_colors.append("lightgreen" if status == "active" else default_color)

    pos = nx.spring_layout(graph)
    edge_labels = nx.get_edge_attributes(graph, 'task')

    nx.draw(graph, pos, node_color=node_colors, with_labels=True, node_size=2000, arrows=True)
    nx.draw_networkx_labels(graph, pos, labels=labels)
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)

    plt.title(title)
    plt.show()

# Example usage:
if __name__ == "__main__":
    from src.graph.workflow_orchestrator import WorkflowOrchestrator

    orchestrator = WorkflowOrchestrator()
    orchestrator.sync_with_registry()  # Automatically populate graph from the registry

    # Visualize using registry-based dynamic labels
    visualize_with_registry_data(orchestrator.graph, "Dynamic Registry-Based Visualization")

    # Example external metrics (if available)
    external_data = {
        "chat_agent": {"load": 0.5, "performance": 0.8},
        "intent_agent": {"load": 0.3, "performance": 0.9},
    }
    visualize_metric_graph(orchestrator.graph, external_data, "Dynamic Metric-Enriched Visualization")
```

---

## Integration with Other Modules

### Agent Registry & Decision-Making Module

- **Live Data Source:**  
  The visualization components pull live metadata from the Agent Registry. As the registry updates (whether by agent managers or the decision-making module), these changes are immediately reflected in the graph.
  
### Agent Managers

- **Event Feedback:**  
  Agent Managers push task delegation and completion events to the system, which are then incorporated into the live graph updates. This ensures that the visualization always reflects the current system state.

---

## Usage and Configuration

### Running the Visualization

- **Standalone Mode:**  
  Run the visualization script directly:
  ```bash
  python src/graph/workflow_visualisation.py
  ```
- **Integrated Mode:**  
  In production, the visualization component can be integrated into a dashboard that continuously updates as events are received.

### Customization Options

- **Layout Algorithms & Styling:**  
  Adjust layout parameters (e.g., spring layout) and styling options (node colors, sizes) within the visualization functions.
- **Metric Integration:**  
  Extend or modify how external metrics are merged with registry data for more detailed node labeling.

---

## Use Cases

- **Real-Time Monitoring:**  
  Operators can use the visualization to monitor task flows and agent interactions in real time.
- **Debugging & Analysis:**  
  Developers can inspect the graph to identify and troubleshoot issues with task routing.
- **Performance Optimization:**  
  By visualizing load and performance metrics, system administrators can fine-tune agent configurations and routing algorithms.

---

## Troubleshooting

- **Graph Not Updating:**  
  Ensure the Agent Registry is current and that events are being properly emitted from the decision-making module.
- **Visualization Rendering Issues:**  
  Verify that all required libraries (NetworkX, Matplotlib) are installed and that layout parameters are appropriately configured.

---

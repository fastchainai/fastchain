# Graph Workflow

The Graph Workflow Orchestrator is a critical component of the multi-agent system that provides real-time visualization of agent interactions, task flows, and overall workflow state. It leverages a dynamic, graph-based representation to help developers, operators, and administrators understand, monitor, and debug the routing and execution of tasks among agents.

---

## Table of Contents

- [Graph Workflow](#graph-workflow)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Architecture](#architecture)
  - [Implementation Details](#implementation-details)
    - [Key Features](#key-features)
  - [Integration with Other Modules](#integration-with-other-modules)
    - [Agent Registry \& Decision-Making Module](#agent-registry--decision-making-module)
    - [Agent Managers](#agent-managers)
  - [Usage and Configuration](#usage-and-configuration)
    - [Running the Orchestrator](#running-the-orchestrator)
    - [Configuration Options](#configuration-options)
  - [Use Cases](#use-cases)
  - [Future Enhancements](#future-enhancements)
  - [Troubleshooting](#troubleshooting)

---

## Overview

The Graph Workflow Orchestrator automatically constructs and updates a directed graph that reflects the current state of the multi-agent system. It is designed to:

- **Visualize Workflows:** Display real-time task flows and interactions between agents.
- **Monitor System State:** Provide insights into agent performance and task delegation.
- **Facilitate Debugging:** Quickly identify bottlenecks or misrouted tasks.
- **Support Dynamic Routing:** Update itself automatically by pulling live data from the Agent Registry.

---

## Architecture

The Orchestrator is built using standard Python libraries:

- **Graph Construction:**  
  Uses [NetworkX](https://networkx.org/) to represent agents as nodes and task flows as directed edges.
  
- **Data Ingestion:**  
  Automatically synchronizes with the Agent Registry to add nodes for all active agents and to generate edges based on agent metadata (such as a defined `"tasks"` list).

- **Visualization Layer:**  
  Uses [Matplotlib](https://matplotlib.org/) to render the graph for monitoring or debugging purposes.

- **Dynamic Updates:**  
  Supports both automatic updates from the registry and real-time event updates, ensuring that the graph reflects the current system state without manual intervention.

---

## Implementation Details

The `WorkflowOrchestrator` (see `src/graph/workflow_orchestrator.py`) provides the following capabilities:

- **Synchronization:**  
  The `sync_with_registry()` method queries the Agent Registry to:
  - Add nodes for all agents whose status is `"active"`.
  - Automatically generate edges using each agent’s metadata (e.g., by reading a `"tasks"` field).

- **Runtime Updates:**  
  Methods such as `update_workflow_with_events()` and `add_custom_edge()` allow dynamic modifications based on live events.

- **Visualization:**  
  The `visualize()` method renders the complete graph using Matplotlib, making it easy to see how tasks are being routed among agents.

### Key Features

- **No Hardcoding:**  
  All agents and their relationships are discovered dynamically from the Agent Registry.
- **Real-Time Adaptation:**  
  The graph is rebuilt or updated on demand to reflect changes such as agent status updates or new task flows.
- **Extensibility:**  
  Additional custom edges can be added at runtime without modifying the underlying orchestrator code.

---

## Integration with Other Modules

### Agent Registry & Decision-Making Module

- **Agent Registry:**  
  Provides the central source of truth. The orchestrator queries it to obtain current agent metadata (including status, capabilities, and defined task flows).
- **Decision-Making Module:**  
  When tasks are routed, the Decision-Making Module emits events that the orchestrator uses to update the graph, ensuring transparency in routing decisions.

### Agent Managers

- **Task Delegation Feedback:**  
  Agent Managers report task delegation events, which are ingested by the orchestrator to reflect interactions between agents in the workflow graph.

---

## Usage and Configuration

### Running the Orchestrator

- **Standalone Mode:**  
  To see a snapshot of the current workflow, run:
  ```bash
  python src/graph/workflow_orchestrator.py
  ```
- **Integrated Mode:**  
  In production, the orchestrator can run as a continuously updating service that listens to message queues or event streams.

### Configuration Options

- **Graph Layout:**  
  Customize the node layout (spring, circular, etc.) in the visualization.
- **Styling:**  
  Adjust node colors, sizes, and edge labels to incorporate performance metrics or load indicators.
- **Event Sources:**  
  Define and integrate with event sources to automatically update the graph.

---

## Use Cases

- **Monitoring:**  
  Real-time visualization helps operators monitor the flow of tasks and agent interactions.
- **Debugging:**  
  Quickly identify misrouted tasks or overloaded agents.
- **Performance Analysis:**  
  Combine with performance metrics to optimize task routing.
- **Auditing:**  
  Historical snapshots of the workflow provide valuable audit trails.

---

## Future Enhancements

- **Interactive Dashboards:**  
  Integration with web-based frameworks (e.g., D3.js) for interactive, zoomable graphs.
- **Automated Alerts:**  
  Implement visual alerts for conditions like agent overload.
- **Historical Data Analysis:**  
  Incorporate time-series data to analyze trends in task flows and performance.

---

## Troubleshooting

- **Graph Not Updating:**  
  Verify that the Agent Registry is up-to-date and that the orchestrator is correctly syncing.
- **Visualization Issues:**  
  Ensure required libraries (NetworkX, Matplotlib) are installed and review layout parameters if nodes overlap.
- **Performance:**  
  For large graphs, consider incremental updates or partial rendering to maintain responsiveness.

---

*For more details on visualization options and customization, refer to the [Graph Workflow Visualization documentation](./graph_visualisation.md).*
```

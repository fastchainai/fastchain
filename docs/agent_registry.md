# Agent Registry

The Agent Registry module serves as the centralised repository for metadata related to all agents in the multi-agent system. It is a critical component for enabling dynamic task routing, performance monitoring, and system orchestration.

---

## Table of Contents

- [Agent Registry](#agent-registry)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Architecture and Design](#architecture-and-design)
    - [Key Features](#key-features)
  - [File Structure](#file-structure)
  - [Core Functionality](#core-functionality)
    - [Initialisation](#initialisation)
    - [Registering an Agent](#registering-an-agent)
    - [Updating an Agent](#updating-an-agent)
    - [Retrieving Agent Data](#retrieving-agent-data)
    - [Unregistering an Agent](#unregistering-an-agent)
  - [Integration with Other Modules](#integration-with-other-modules)
    - [Decision-Making Module](#decision-making-module)
    - [Graph Workflow Orchestrator](#graph-workflow-orchestrator)
    - [Agent Managers](#agent-managers)
  - [Best Practices](#best-practices)
  - [Example JSON and Usage](#example-json-and-usage)
    - [Sample `registry.json`](#sample-registryjson)
    - [Usage Example](#usage-example)

---

## Overview

The Agent Registry is responsible for storing and managing metadata for each agent in the system. This metadata includes:
- **Identification:** Unique agent name and version.
- **Capabilities:** Functions the agent can perform (e.g., chat, intent classification, retrieval, reasoning).
- **Status:** Operational state (active, inactive, etc.).
- **Configuration:** Endpoints, environment details, and other operational settings.
- **Operational Metrics:** Performance data, load, and timestamps (creation and last update).

The Registry ensures that dynamic components—such as the Decision-Making Module and Graph Workflow Orchestrator—have access to up-to-date agent information for routing tasks and monitoring system health.

---

## Architecture and Design

The Agent Registry is implemented as a singleton to ensure that there is only one central source of truth for all agent metadata. It reads from and writes to a persistent JSON file (e.g., `registry.json`), ensuring that the state of the system is maintained across application restarts.

### Key Features

- **Persistence:**  
  Uses a JSON file to persist metadata, allowing the system to recover the state after a restart.

- **Singleton Pattern:**  
  Guarantees a single instance of the registry throughout the application, ensuring consistent data management.

- **API Methods:**  
  Provides methods to register, update, retrieve, list, and unregister agents.

- **Integration:**  
  The Decision-Making Module and other orchestration tools query the registry to make dynamic, data-driven decisions.

---

## File Structure

The relevant files for the Agent Registry are located under `src/agents/`:

```plaintext
src/
└── agents/
    ├── registry.py      # Agent Registry module
    └── registry.json    # Persistent storage for agent metadata
```

- **registry.py:**  
  Contains the implementation of the Agent Registry, including all API methods for managing agent metadata.

- **registry.json:**  
  A JSON file used for persisting the registry data between application sessions.

---

## Core Functionality

### Initialisation

When the registry is initialised, it:
- Checks for the existence of `registry.json`.
- Loads agent metadata if the file exists.
- Initialises an empty registry if the file is missing or corrupt.

### Registering an Agent

- **Method:** `register_agent(agent_name: str, metadata: dict)`
- **Purpose:**  
  Adds a new agent to the registry. If the agent is already registered, a `ValueError` is raised.
- **Usage:**  
  Called by an agent’s manager during startup to announce its presence and capabilities.

### Updating an Agent

- **Method:** `update_agent(agent_name: str, metadata: dict)`
- **Purpose:**  
  Modifies the metadata for an existing agent. Used to update agent status, capabilities, or operational metrics.
- **Usage:**  
  Agents (or their managers) call this method when there is a change in their state (e.g., transitioning from inactive to active, updated load metrics).

### Retrieving Agent Data

- **Method:** `get_agent(agent_name: str) -> dict`
- **Purpose:**  
  Retrieves metadata for a specific agent.
- **Method:** `get_all_agents() -> dict`
- **Purpose:**  
  Returns the metadata for all registered agents.
- **Usage:**  
  Utilised by the Decision-Making Module and Graph Workflow Orchestrator for task routing and system monitoring.

### Unregistering an Agent

- **Method:** `unregister_agent(agent_name: str)`
- **Purpose:**  
  Removes an agent from the registry. Used when an agent is decommissioned or permanently taken offline.
- **Usage:**  
  Helps maintain an accurate and up-to-date registry by removing stale entries.

---

## Integration with Other Modules

### Decision-Making Module

- **Function:**  
  The Decision-Making Module queries the Agent Registry to decide which agent is best suited for a task based on:
  - Capabilities (from `agent.json` metadata)
  - Current status (active/inactive)
  - Real-time performance and load metrics
- **Impact:**  
  Accurate registry data ensures that tasks are routed to agents that are available and capable, optimising system performance and reliability.

### Graph Workflow Orchestrator

- **Function:**  
  Visualises the system’s state by retrieving metadata from the registry.
- **Impact:**  
  Helps operators and developers see which agents are active, their performance, and how tasks flow through the system.

### Agent Managers

- **Function:**  
  Each agent’s manager registers and updates the agent’s metadata in the registry at startup and during runtime.
- **Impact:**  
  Ensures that every agent accurately reports its state and capabilities, facilitating system-wide coordination.

---

## Best Practices

- **Consistency:**  
  Always update the agent metadata (`agent.json`) to reflect the current state. This is critical for dynamic decision-making.

- **Encapsulation:**  
  Agents should be self-contained; all configuration data should reside in their local `agent.json` files and be merged into the central registry.

- **Error Handling:**  
  Implement robust error handling when reading from or writing to the registry. If `registry.json` is corrupt, default to a safe state.

- **Regular Updates:**  
  Agents should periodically update the registry to reflect changes in load, performance, or operational status.

- **Security:**  
  Ensure that access to the registry (both programmatically and the JSON file) is secure, to prevent unauthorised modifications.

---

## Example JSON and Usage

### Sample `registry.json`

```json
{
    "chat_agent": {
        "agent_name": "chat_agent",
        "version": "1.0",
        "capabilities": ["chat"],
        "status": "active",
        "created_at": "2023-10-01T12:00:00Z",
        "last_updated": "2023-10-01T12:00:00Z",
        "configuration": {
            "endpoint": "http://localhost:8000/chat",
            "environment": "development"
        },
        "performance": {
            "response_time_ms": 120,
            "error_rate": 0.01
        },
        "load": {
            "current_tasks": 3,
            "max_tasks": 10
        }
    },
    "intent_agent": {
        "agent_name": "intent_agent",
        "version": "1.0",
        "capabilities": ["intent", "routing"],
        "status": "active",
        "created_at": "2023-10-01T12:00:00Z",
        "last_updated": "2023-10-01T12:00:00Z",
        "configuration": {
            "endpoint": "http://localhost:8000/intent",
            "environment": "development"
        }
    }
}
```

### Usage Example

An agent’s manager (e.g., for `chat_agent`) will:
- Load its local configuration from `agent.json`.
- Call `AgentRegistry.get_instance().register_agent("chat_agent", metadata)` at startup.
- Update its state in the registry using `update_agent()` when significant changes occur.

---
# Agent Development Guidelines

This document outlines comprehensive design guidelines for developers tasked with building agents for our multi-agent system. It details the folder structure, purpose of each file, shared modules, and best practices for ensuring each agent is self-contained yet seamlessly integrated into the broader ecosystem.

---

## Table of Contents

- [Agent Development Guidelines](#agent-development-guidelines)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Agent Folder Structure](#agent-folder-structure)
  - [Detailed File Descriptions](#detailed-file-descriptions)
    - [`__init__.py`](#__init__py)
    - [`agent.json`](#agentjson)
    - [`agent.py`](#agentpy)
    - [`manager.py`](#managerpy)
    - [`task_engine.py`](#task_enginepy)
    - [`utils.py`](#utilspy)
    - [`context.py` (Optional)](#contextpy-optional)
  - [Shared Modules and Global Components](#shared-modules-and-global-components)
  - [Best Practices](#best-practices)

---

## Overview

Each agent in our system is designed to be a self-contained unit. This means that all of its logic, configuration, and state management is encapsulated within its own directory. Agents interact with shared modules—such as the Agent Registry, Decision-Making Module, and Graph Workflow Orchestrator—to achieve dynamic task routing, monitoring, and inter-agent communication.

The aim of these guidelines is to ensure consistency, maintainability, and ease of integration for every agent developed within the system. By adhering to these principles, developers can build robust agents that are easy to test, update, and deploy independently.

---

## Agent Folder Structure

Each agent is located within its own directory under `src/agents/`. For example, an Intent Agent might have the following structure:

```md
src/
└── agents/
    ├── intent_agent/
    │   ├── __init__.py
    │   ├── agent.json            # Agent metadata
    │   ├── agent.py              # Agent entry point
    │   ├── manager.py            # Agent Manager (orchestration layer)
    │   ├── task_engine.py        # Langchain chains for the agent
    │   ├── utils.py              # Agent-specific helper functions
    │   └── context.py            # (Optional) Agent-specific context handling
    ├── ...                       # Future agents
    └── registry/                 # Shared central registry (e.g. registry.py, registry.json)
```

Each file and folder in this structure serves a distinct purpose to promote modularity and separation of concerns.

---

## Detailed File Descriptions

### `__init__.py`

- **Purpose:**  
  Initialises the agent’s package. This file should be kept minimal and may be used to expose key components.

- **Developer Guidelines:**  
  Do not include heavy logic here. Use this file only to indicate that the folder is a Python package.

### `agent.json`

- **Purpose:**  
  Contains all the metadata for the agent. This includes:
  - Agent name and version.
  - Capabilities (e.g. "intent", "retrieval", "chat", "reasoning").
  - Status (active/inactive).
  - Operational configuration (endpoint URLs, environment, etc.).
  - Optional metrics such as creation date, last updated, and performance data.

- **Developer Guidelines:**  
  - Ensure that this file is kept up to date with any changes in the agent’s configuration.
  - The metadata from `agent.json` is merged into the central Agent Registry, which is critical for the Decision-Making Module and monitoring tools.
  - Filename standardisation: each agent’s metadata file should simply be called `agent.json` for consistency.

### `agent.py`

- **Purpose:**  
  Serves as the main entry point for the agent. It initialises the agent’s components and starts its operations.

- **Developer Guidelines:**  
  - Include code to load configuration from `agent.json`.
  - Initialise the Agent Manager and any other key services.
  - Handle any necessary startup routines and error logging.

### `manager.py`

- **Purpose:**  
  Acts as the orchestration layer for the agent. The Agent Manager is responsible for managing the agent’s lifecycle (starting, stopping, and updating state) and delegating tasks.

- **Developer Guidelines:**  
  - Ensure that the manager registers the agent with the central Agent Registry at startup.
  - Update the registry when the agent’s status or operational parameters change.
  - Implement clear interfaces for task delegation, ideally integrating with the Decision-Making Module if routing is required.
  - Keep the code modular and well-documented to ease future maintenance.

### `task_engine.py`

- **Purpose:**  
  Implements the processing chains using Langchain (or a similar framework). This is where the core business logic for the agent is defined.

- **Developer Guidelines:**  
  - Structure the chain so that individual steps (e.g. pre-processing, model invocation, post-processing) are clearly separated.
  - Ensure the task engine logs important events for debugging and monitoring purposes.
  - Keep the chains modular so that they can be updated or replaced without affecting other components.

### `utils.py`

- **Purpose:**  
  Houses helper functions and utilities that are specific to the agent’s operation.

- **Developer Guidelines:**  
  - Write clear, reusable functions to avoid duplicating code.
  - Document each function with its purpose, input parameters, and expected outputs.
  - Ensure that utilities are designed to be as generic as possible within the context of the agent.

### `context.py` (Optional)

- **Purpose:**  
  Manages agent-specific context, such as conversation state or session data, ensuring continuity across multiple interactions.

- **Developer Guidelines:**  
  - Implement functions for setting, updating, and retrieving context.
  - Keep context management separate from the core logic to maintain clarity.
  - Only include this file if the agent requires persistent state management beyond simple request handling.

---

## Shared Modules and Global Components

Agents should leverage shared modules to ensure consistency and reduce duplication. Key shared components include:

- **Agent Registry:**  
  - Centralised repository for agent metadata.
  - Critical for dynamic task routing by the Decision-Making Module.
  - Ensure that each agent registers its metadata from `agent.json` to the central registry.

- **Decision-Making Module:**  
  - Uses data from the Agent Registry to decide task routing.
  - Queries metadata such as capabilities, load, and performance.

- **Graph Workflow Orchestrator:**  
  - Visualises the workflow of tasks between agents.
  - Receives events from Agent Managers and updates a real-time graphical representation.

By leveraging these shared modules, each agent can focus on its domain-specific functionality while still integrating seamlessly with the overall system.

---

## Best Practices

- **Self-Containment:**  
  Each agent must be self-contained. All agent-specific logic, configuration, and state management should reside within its own directory.

- **Clear Separation of Concerns:**  
  Use designated files for specific responsibilities. For example, the Agent Manager handles orchestration, while the Task Execution Engine focuses solely on processing logic.

- **Consistent Metadata Management:**  
  Maintain an up-to-date `agent.json` file for each agent. This is vital for accurate routing and monitoring by the Decision-Making Module.

- **Loose Coupling:**  
  Design agents so that they interact with shared modules via well-defined APIs. This ensures that changes in one module do not necessitate modifications in individual agents.

- **Extensive Documentation and Logging:**  
  Document code thoroughly and implement robust logging mechanisms. This aids in debugging and ensures that future developers can easily understand and maintain the system.

---
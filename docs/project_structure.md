# Project Structure

This document describes the overall architecture and organization of the multi-agent system project. The structure is designed to promote modularity, scalability, and maintainability while ensuring that each agent is self-contained yet fully integrated with shared modules for orchestration, decision-making, and workflow visualization.

---

## 1. Overview

The project is organised into several key directories, each serving a distinct purpose:

- **`src/`** 
  Contains all source code organized into subdirectories for agents, shared modules, routing, and integrations.

- **`tests/`**
  Includes unit, integration, and end-to-end tests to ensure the reliability of individual components and the system as a whole.

- **`scripts/`** 
  Houses deployment, migration, and utility scripts used for managing the project.

- **`docs/`** 
  Contains documentation files that detail the system’s architecture, guidelines, and best practices.

- **Configuration and metadata files:**  
  Files like `.env`, `Dockerfile`, `pyproject.toml`, and `README.md` provide necessary configurations, dependency management, and overall project information.

---

## 2. Detailed Directory Structure

Below is an annotated breakdown of the key directories and files within the `src/` folder:

```md
src/
├── agents/
│   ├── intent_agent/             # Example: Intent Agent - processes user queries and classifies intent
│   │   ├── __init__.py           # Package initializer for the Intent Agent
│   │   ├── agent.json            # Agent metadata file (e.g., name, version, capabilities, configuration)
│   │   ├── agent.py              # Agent entry point; responsible for initialization and startup routines
│   │   ├── manager.py            # Agent Manager; controls the agent's lifecycle, state, and task delegation
│   │   ├── task_engine.py        # Task Execution Engine; implements chain-based processing (e.g., using Langchain)
│   │   ├── utils.py              # Helper functions specific to the Intent Agent
│   │   └── context.py            # (Optional) Manages agent-specific context and session data
│   ├── ...                       # Additional agents (e.g., chat_agent, retrieval_agent, reasoning_agent)
│   ├── registry.json             # Persistent storage for the central Agent Registry (aggregated metadata for all agents)
│   └── registry.py               # Central Agent Registry module; provides functions to register, update, and query agents
│
├── api/                         # API endpoints for external interaction (e.g., FastAPI application)
│   └── ...                      # Versioned APIs, endpoints, dependencies, and schema definitions
│
├── routing/                     # Modules for dynamic task routing within the multi-agent system
│   └── decision_maker.py        # Decision-Making Module; selects the optimal agent based on metrics, capabilities, and load
│
├── graph/                       # Modules for workflow visualization and orchestration
│   ├── __init__.py              # Package initializer for the graph module
│   ├── workflow_orchestrator.py # Visualizes and monitors workflows using LangGraph (or similar frameworks)
│   └── workflow_visualization.py# Additional visualization utilities for graphing workflows and task flows
│
├── context/                     # Centralized context management shared across agents
│   └── context_manager.py       # Provides functions to manage and share context among agents
│
├── models/                      # Contains abstract models and concrete implementations for language and AI models
│   ├── __init__.py
│   ├── base_model.py            # Abstract base model definitions
│   ├── langchain_model.py       # Extends the base model with Langchain functionalities
│   ├── chat_model.py            # Example: ChatModel extending LangchainModel for chat operations
│   └── ...                      # Optional additional model implementations
│
├── tools/                       # Shared tools and utilities that can be leveraged by any agent
│   ├── __init__.py
│   ├── base_tool.py             # Base classes for tool abstraction
│   ├── discovery.py             # Dynamic tool discovery and adaptation system
│   ├── exceptions.py            # Custom exceptions related to tool operations
│   └── ...                      # Additional custom tools as required
│
├── communication/               # Modules for managing inter-agent and external communication
│   ├── __init__.py
│   └── communication.py         # General utilities for standardized communication protocols
│
├── adapters/                    # Implementations of connectors for external APIs and services
│   ├── __init__.py
│   ├── openai_adapter.py        # Adapter to interact with the OpenAI API
│   ├── vault_adapter.py         # Adapter for interfacing with Hashicorp Vault
│   └── ...                      # Other adapters to integrate with external service APIs
│
├── learning/                    # Modules that handle feedback and agent updates based on performance
│   ├── __init__.py
│   ├── feedback_manager.py      # Collects and processes feedback signals from agents
│   └── updater.py               # Updates agent behavior or model parameters based on feedback
│
├── config/                      # Configuration files and modules (e.g., Dynaconf)
│   ├── __init__.py
│   ├── config.py
│   ├── settings.toml
│   ├── .secrets.toml
│   └── ...                      # Additional configuration files as needed
│
└── utils/                       # General utility functions and shared helpers
    ├── __init__.py
    └── ...                      # Other helper functions used across multiple modules
```

---

## 3. Key Components and Their Interactions

### Agent-Specific Directories (e.g., `intent_agent`)

- **Agent Self-Containment:**  
  Each agent (e.g., `intent_agent`) is self-contained. It includes its metadata (`agent.json`), core functionality (`agent.py`), lifecycle management (`manager.py`), task processing logic (`task_engine.py`), and any helper functions (`utils.py`).  
  This encapsulation ensures that the agent can be developed, tested, and deployed independently without tight coupling to other parts of the system.

- **Agent Metadata:**  
  The `agent.json` file contains crucial information such as:
  - **agent_name:** Unique identifier.
  - **version:** Current version of the agent.
  - **capabilities:** A list of functionalities provided by the agent (e.g., intent processing, routing).
  - **status:** Operational state (active/inactive).
  - **configuration:** Endpoint URLs, environment settings, and other configuration parameters.  
  This metadata is critical for integration with the Agent Registry and informs the Decision-Making Module about each agent’s capabilities and operational status.

---

## 4. Shared Modules

- **Agent Registry:**  
  - **Files:** `agents/registry.py`, `agents/registry.json`  
  - **Description:**  
    Centralizes metadata for all agents by providing functions to register, update, and query agent information. This is critical for the Decision-Making Module to determine task routing and monitor system health.

- **Decision-Making Module:**  
  - **File:** `routing/decision_maker.py`  
  - **Description:**  
    Uses metadata from the Agent Registry along with runtime metrics (load, performance, etc.) to make informed decisions on task routing. It dynamically assigns tasks to the best-suited agent, optimizing resource utilization and overall system performance.

- **Graph Workflow Orchestrator and Visualization:**  
  - **Files:** `graph/workflow_orchestrator.py`, `graph/workflow_visualization.py`  
  - **Description:**  
    Provides graph-based visualization and monitoring of workflows. It displays interactions between agents and offers customized dashboards to depict task flows, performance metrics, and routing decisions in real time.

- **Context Manager:**  
  - **File:** `context/context_manager.py`  
  - **Description:**  
    Offers shared context management functions to maintain state and ensure continuity during multi-step processes. This is vital for tasks that span multiple agents or require historical context.

- **Models:**  
  - **Files:** `models/base_model.py`, `models/langchain_model.py`, `models/chat_model.py`, etc.  
  - **Description:**  
    Contains abstract models and concrete implementations for language and AI models. These modules standardize model interfaces across agents, ensuring consistency in how agents process language and perform inference.

- **Tools:**  
  - **Files:** `tools/base_tool.py`, `tools/discovery.py`, `tools/exceptions.py`, etc.  
  - **Description:**  
    Provides reusable components for common operations and external functionality. These tools help with data processing, dynamic tool discovery, and error handling, promoting consistency and ease of maintenance.

- **Communication:**  
  - **File:** `communication/communication.py`  
  - **Description:**  
    Implements standardized utilities for inter-agent and external communication. This module ensures robust and secure message exchanges between agents and external systems.

- **Adapters:**  
  - **Files:** `adapters/openai_adapter.py`, `adapters/vault_adapter.py`, etc.  
  - **Description:**  
    Provides connectors for external APIs and services. These adapters abstract protocol details, facilitating seamless integration with third-party platforms and external systems.

- **Learning:**  
  - **Files:** `learning/feedback_manager.py`, `learning/updater.py`  
  - **Description:**  
    Handles the collection of feedback and updates to agent behavior or models. This module enables agents to adapt and improve based on performance metrics and user feedback.

- **Config:**  
  - **Files:** `config/config.py`, `config/settings.toml`, `config/.secrets.toml`, etc.  
  - **Description:**  
    Centralizes configuration management using Dynaconf, handling environment-specific settings and securing sensitive data. It ensures consistency across deployments and simplifies configuration management.

- **Utils:**  
  - **Directory:** `utils/`  
  - **Description:**  
    Contains general utility functions and shared helpers used across various modules. These utilities reduce code duplication and simplify maintenance by providing common functions accessible system-wide.

---

## 5. Importance of the Central Registry and Shared Modules

- **Central Agent Registry:**  
  The registry is the backbone of the multi-agent system. It maintains an up-to-date view of each agent’s capabilities, status, and configuration. Modules like the Decision-Making Module use this information to make real-time routing decisions.  
  - **Persistence:** By storing data in `registry.json`, the system retains agent state across restarts.
  - **Consistency:** Ensures that all agents are recognized and that their operational data is accurate, enabling efficient coordination and monitoring.

- **Shared Modules:**  
  These modules (such as the Decision-Making Module, Graph Workflow Orchestrator, and Context Manager) promote reuse and reduce duplication of code. They standardize common functionalities like communication, error handling, and logging, which simplifies development and maintenance.

---

## 6. Best Practices

- **Self-Containment:**  
  Each agent should be self-contained, with its own metadata, processing logic, and lifecycle management. This isolation facilitates independent development, testing, and deployment.

- **Modularity:**  
  Shared modules must be designed for reuse. Keep functionality decoupled, and use clear interfaces to interact with these modules.

- **Clear Separation of Concerns:**  
  Maintain clear boundaries between different components (e.g., task processing vs. communication vs. configuration). This aids in debugging, scaling, and maintaining the system.

- **Regular Updates:**  
  Ensure that agent metadata in `agent.json` and the central registry is updated consistently to reflect the true state of the agent. This is vital for the Decision-Making Module and monitoring systems.

- **Comprehensive Documentation:**  
  Document each module and component thoroughly to facilitate onboarding and future development. This document serves as a reference for how the system is structured and how components interact.

---

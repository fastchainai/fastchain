# FastChain AI

FastChain AI is a modular, dynamically configurable multi-agent framework that enables autonomous intent classification and intelligent task routing, enhanced with comprehensive system monitoring and user-friendly diagnostic capabilities.

## Overview

FastChain AI combines FastAPI's speed with Langchain's modular chain-based logic to create an efficient, scalable AI application platform. The framework is designed to handle complex workflows through a system of specialized agents that can process, route, and execute tasks based on user intent.

## Key Features
- **Modular Agent Architecture**
- **Dynamic Task Routing**
- **System Monitoring**

---

## Architecture

The project follows a modular architecture with clear separation of concerns.

Key directories and files within the `src/` folder:

### Agent-Specific Directories (`src/agents`)

- **Agent Self-Containment:**
    Each agent is self-contained within its own directory. This ensures that an agent can be developed, tested, and deployed independently.

- **Agent Metadata:**
    The `agent.json` file contains crucial information (agent name, version, capabilities, status, config) for integration with the Agent Registry and informs the Decision-Making Module about each agent’s capabilities and operational status.

- **Agent Registry:**
    The registry is the backbone of the multi-agent system. It maintains an up-to-date view of each agent’s capabilities, status, and configuration. The Decision-Making Module use this information to make real-time routing decisions and monitor system health.

---

- **Example Agent:**
    For example, a Chat Agent might have the following structure:

```md
src/
└── agents/
    ├── chat_agent/               # Agent Package (Example: Chat Agent)
    │   ├── __init__.py           # Package initializer for the Agent
    │   ├── agent.json            # Agent metadata
    │   ├── agent.py              # Agent entry point
    │   ├── manager.py            # Agent Manager (controls the Agent)
    │   ├── task_engine.py        # Task Execution Engine (chain-based processing)
    │   ├── utils.py              # Agent-specific helper functions
    │   └── context.py            # (Optional) Agent-specific context handling
    ├── ...                       # Future agents
    └── registry.py               # Central Agent Registry (e.g. registry.py, registry.json)
```
The Agent automatically registers itself on the Agent Registry. Making it available to other agents.

---

### Shared Modules

These modules (such as the Decision-Making Module, Graph Workflow Orchestrator, and Context Manager) promote reuse and reduce duplication of code. They standardize common functionalities like communication, error handling, and logging, which simplifies development and maintenance.

```md
src/
├── routing/         # Decision making and task routing
├── context/         # Maintaing context across Agents
├── graph/           # Workflow orchestration
├── learning/        # Agent feedback loop and learning
├── models/          # AI/ML model implementations
├── tools/           # Shared agent tools
├── communication/   # Standardises inter-Agent and external communication
├── adapters/        # Connectors for external APIs and services
├── config/          # Centralises configuration management using Dynaconf
└── ultils/          # General utility functions and shared helpers
```

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

## Documentation

Detailed documentation is available in the `docs/` directory:

---

## Support

For support, feature requests, or bug reports, please [open an issue](https://github.com/fastchainai/fastchain/issues).

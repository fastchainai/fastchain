# Agent Manager

## Overview

The Agent Manager is a critical component responsible for orchestrating an individual agent's lifecycle within the multi-agent system. It encapsulates core functions such as initialization, registration, state management, task delegation, and context handling. By maintaining a well-defined interface, the Agent Manager ensures that the agent remains self-contained while seamlessly integrating with shared system modules—especially the Agent Registry and Decision-Making Module.

## Responsibilities

The primary responsibilities of the Agent Manager include:

- **Lifecycle Management:**  
  - **Initialization:** Load configuration and metadata from the agent’s `agent.json` file.
  - **Startup:** Activate the agent and register it with the central Agent Registry.
  - **Shutdown/Deactivation:** Update the registry and clean up resources when the agent stops.

- **State Management:**  
  - Maintain conversation context or any agent-specific state.
  - Update and persist dynamic state changes to the Agent Registry for accurate system-wide monitoring.

- **Task Delegation:**  
  - Interface with the Decision-Making Module to route incoming tasks.
  - Forward tasks either to internal components (via the Task Execution Engine) or to other agents based on the task requirements.

- **Registry Interaction:**  
  - Register the agent on startup and update metadata (such as status or context size) as necessary.
  - Ensure that the Agent Registry holds an up-to-date record of the agent’s operational status, capabilities, and other metadata.

## File Structure and Key Components

Within an agent’s folder (for example, `intent_agent` or `chat_agent`), the `manager.py` file serves as the Agent Manager. The key components of the file are:

### 1. Initialization

- **Loading Metadata:**  
  The manager loads its configuration from the dedicated `agent.json` file. This file contains essential details like agent name, version, capabilities, and initial status.

- **Registry Setup:**  
  The manager retrieves the singleton instance of the Agent Registry. This enables the agent to register itself and update its metadata dynamically during its lifecycle.

### 2. Starting the Agent

- **Activation:**  
  On startup, the Agent Manager sets the agent’s status to "active" and registers the agent with the central registry.

- **Registry Registration:**  
  If the agent is not yet registered, it calls the `register_agent` method; if already registered, it calls `update_agent` to reflect any changes.

### 3. Task Delegation

- **Integration with Decision-Making:**  
  When a task is received (for example, a user query), the Agent Manager may delegate the task to either an internal module (via the Task Execution Engine) or forward it to another agent using the Decision-Making Module.

- **Logging and Monitoring:**  
  Each task delegation is logged for troubleshooting and can trigger updates in the workflow orchestrator.

### 4. Context and State Management

- **Conversation/Session State:**  
  The Agent Manager keeps a record of the current context, ensuring continuity in interactions.

- **Dynamic Updates:**  
  Changes in the agent’s state (e.g., context size) are periodically sent to the Agent Registry, which is critical for monitoring and decision-making.

## Example Implementation

Below is a simplified example of an Agent Manager implementation (for a Chat Agent) that demonstrates the integration of all these components:

```python
# src/agents/chat_agent/manager.py

import json
from src.agents.registry import AgentRegistry

class ChatAgentManager:
    def __init__(self, metadata_file="src/agents/chat_agent/agent.json"):
        # Load agent metadata from the JSON file.
        with open(metadata_file, "r") as f:
            self.metadata = json.load(f)

        self.agent_name = self.metadata.get("agent_name", "chat_agent")
        self.version = self.metadata.get("version", "1.0")
        self.capabilities = self.metadata.get("capabilities", ["chat"])
        self.status = self.metadata.get("status", "inactive")

        # Initialize conversation context.
        self.conversation_context = {}

        # Get the singleton instance of the Agent Registry.
        self.registry = AgentRegistry.get_instance()

    def start_agent(self):
        self.status = "active"
        # Update in-memory metadata.
        self.metadata["status"] = self.status

        # Register or update the agent in the central registry.
        try:
            self.registry.register_agent(self.agent_name, self.metadata)
        except ValueError:
            self.registry.update_agent(self.agent_name, {"status": self.status})

        print("Chat Agent started and ready to handle queries.")

    def delegate_task(self, task):
        # Integrate with the Decision-Making Module as needed.
        print(f"Delegating task: {task}")
        # This is where you would invoke the decision-making module,
        # e.g., selected_agent = decision_maker.route_task("intent")
        # and forward the task accordingly.

    def update_context(self, message, response):
        self.conversation_context[message] = response
        # Optionally update the registry with context metrics.
        self.registry.update_agent(self.agent_name, {"context_size": len(self.conversation_context)})

# Example usage:
if __name__ == "__main__":
    manager = ChatAgentManager()
    manager.start_agent()
    manager.delegate_task("Process new user query")
```

## Integration with Shared Modules

The Agent Manager is designed to leverage shared modules for a unified system experience:

- **Agent Registry:**  
  Acts as the single source of truth for all agent metadata. The Manager must ensure that any change in the agent’s state is reflected in the registry. This is critical for:
  - **Routing Decisions:** The Decision-Making Module queries the registry to select the appropriate agent for a task.
  - **Monitoring:** The Graph Workflow Orchestrator and other monitoring tools rely on accurate registry data to visualize system performance.

- **Task Execution Engine:**  
  A shared module that processes the business logic of the agent’s tasks. The Manager delegates tasks to this engine when necessary.

- **Decision-Making Module:**  
  The Manager works in tandem with the Decision-Making Module to route tasks dynamically based on real-time metrics and agent capabilities stored in the registry.

- **Graph Workflow Orchestrator:**  
  Although not directly part of the Agent Manager, the events logged by the Manager (e.g., task delegation) are used by the Graph Workflow Orchestrator to visualize agent interactions and workflow paths.

## Best Practices

- **Self-Containment:**  
  Ensure that the agent is fully self-contained. All configuration should reside in the `agent.json` file, and the Manager should use this configuration without hardcoding values.

- **Regular Registry Updates:**  
  Always update the registry on state changes to maintain an accurate, real-time overview of system status. This is critical for dynamic routing and load balancing.

- **Clear Separation of Concerns:**  
  The Manager should focus on orchestration and state management, while the Task Execution Engine handles processing logic. This separation promotes maintainability and scalability.

- **Robust Logging and Error Handling:**  
  Implement comprehensive logging within the Manager to facilitate troubleshooting and performance monitoring. Ensure that errors during registration or task delegation are handled gracefully.

---
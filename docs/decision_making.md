# Decision-Making Module

The Decision-Making Module is a central component of our multi-agent system, responsible for dynamically routing tasks to the most suitable agent based on real-time metrics, capabilities, and operational status. This documentation is written in Australian English.

---

## Table of Contents

- [Decision-Making Module](#decision-making-module)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Purpose and Responsibilities](#purpose-and-responsibilities)
    - [Purpose](#purpose)
    - [Responsibilities](#responsibilities)
  - [Architecture and Design](#architecture-and-design)
    - [Key Components](#key-components)
    - [Design Considerations](#design-considerations)
  - [Core Functionality](#core-functionality)
    - [Input and Output](#input-and-output)
    - [Routing Algorithm](#routing-algorithm)
  - [Integration with Other Modules](#integration-with-other-modules)
  - [Usage Examples](#usage-examples)
    - [Example Scenario](#example-scenario)
    - [Code Snippet Example](#code-snippet-example)
  - [Best Practices](#best-practices)

---

## Overview

The Decision-Making Module is designed to be the intelligence behind task routing in our multi-agent system. It ensures that tasks are allocated to the most appropriate agent by evaluating multiple criteria including agent capabilities, load, and performance metrics. By centralising these decisions, the module optimises system efficiency and responsiveness, contributing to an overall robust and adaptive architecture.

---

## Purpose and Responsibilities

### Purpose

- **Dynamic Task Routing:**  
  The module routes incoming tasks to agents that are best equipped to handle them based on a variety of criteria.

- **Optimisation of System Resources:**  
  By balancing load and utilising performance data, it helps prevent bottlenecks and ensures optimal utilisation of agent capabilities.

- **Facilitation of Adaptive Workflows:**  
  It allows the system to dynamically adjust to changes in agent availability and performance, supporting a flexible and resilient workflow.

### Responsibilities

- **Querying the Agent Registry:**  
  Retrieves up-to-date metadata for each agent, such as capabilities, status, and configuration settings.

- **Gathering Real-Time Metrics:**  
  Integrates with monitoring systems to obtain current load and performance data for each agent.

- **Evaluating Task Requirements:**  
  Matches task requirements against the capabilities reported in agent metadata.

- **Scoring and Selection:**  
  Utilises a scoring algorithm to rank candidate agents, ultimately selecting the most suitable one for task execution.

- **Returning Decisions:**  
  Provides a clear output, typically the identifier or endpoint of the selected agent, for subsequent task delegation.

---

## Architecture and Design

### Key Components

- **Input Interface:**  
  A function (or set of functions) that accepts task details and required capabilities.

- **Registry Integration:**  
  Accesses the Agent Registry to obtain metadata for all registered agents.

- **Metrics Collection:**  
  Retrieves dynamic metrics such as current load and performance ratings from external sources or in-memory stores.

- **Routing Algorithm:**  
  Applies a weighted scoring system combining static metadata and dynamic metrics to determine the best agent.

- **Output Interface:**  
  Returns the identifier of the selected agent, facilitating task forwarding by other system components.

### Design Considerations

- **Modularity:**  
  The module is designed to be independent and callable from any part of the system that requires task routing.

- **Extensibility:**  
  The scoring algorithm is modular, allowing easy integration of additional criteria (e.g. geographical location or cost factors) in the future.

- **Robustness:**  
  Built-in error handling ensures that, in the absence of suitable candidates, fallback strategies are implemented (e.g. default routing or round-robin assignment).

---

## Core Functionality

### Input and Output

- **Input:**  
  - Task requirements (e.g. required capability such as "intent", "retrieval", "reasoning").
  - Optionally, additional parameters such as urgency or context details.

- **Output:**  
  - Returns the identifier or endpoint of the selected agent.
  - If no suitable agent is found, returns a null value or an appropriate error indicator.

### Routing Algorithm

1. **Filter Candidates:**  
   - The module first filters all registered agents to identify those that are active and possess the required capability.

2. **Retrieve Metrics:**  
   - It then collects dynamic metrics, including current load and recent performance ratings.

3. **Score Calculation:**  
   - Each candidate agent is assigned a score using a weighted formula. For example:

     ```
     score = (weight_performance * performance_metric) + (weight_load * (1 / (load_metric + constant)))
     ```

     Where:
     - `performance_metric` reflects recent success rates or response times.
     - `load_metric` is a measure of the current operational burden.
     - `weight_performance` and `weight_load` are configurable parameters that determine the importance of each factor.

4. **Agent Selection:**  
   - The agent with the highest score is selected as the optimal candidate for task routing.

5. **Fallback Mechanism:**  
   - If no candidates meet the minimum criteria, the module can return a default agent or trigger a notification for manual intervention.

---

## Integration with Other Modules

- **Agent Registry:**  
  The Decision-Making Module depends on accurate and current data from the Agent Registry. It retrieves metadata such as agent capabilities, status, and configuration settings, which are critical to making informed routing decisions.

- **Graph Workflow Orchestrator:**  
  Routing decisions made by this module are visualised by the Graph Workflow Orchestrator. This integration allows system operators to see real-time task flows and evaluate the efficiency of routing decisions.

- **Agent Managers:**  
  The module's output is used by Agent Managers to forward tasks. For example, a Chat Agent Manager may use it to delegate a conversation processing task to the Intent Agent.

- **Monitoring Systems:**  
  Real-time performance and load metrics are often sourced from integrated monitoring tools. This data is essential for the module to calculate scores accurately.

---

## Usage Examples

### Example Scenario

Suppose a task requires the "retrieval" capability. The Decision-Making Module performs the following:

1. **Filter Agents:**  
   It queries the Agent Registry to identify all agents with the "retrieval" capability that are active.

2. **Retrieve Metrics:**  
   It collects current load and performance metrics for these agents.

3. **Calculate Scores:**  
   Each candidate agent is scored based on the weighted formula. The agent with the highest score is selected.

4. **Return Decision:**  
   The module returns the identifier of the selected agent (e.g., `"retrieval_agent"`), which is then used by the originating module to route the task.

### Code Snippet Example

```python
from decision_maker import route_task

# Example usage:
required_capability = "retrieval"
selected_agent = route_task(required_capability)
if selected_agent:
    print(f"Task will be routed to: {selected_agent}")
else:
    print("No suitable agent found for the task.")
```

---

## Best Practices

- **Keep Data Current:**  
  Ensure that agent metadata in the Agent Registry is up-to-date. Regular updates by Agent Managers are critical to the module’s effectiveness.

- **Configure Weights Appropriately:**  
  Adjust the scoring weights to reflect the priorities of your system. For instance, if performance is more critical than load, increase the weight for performance metrics.

- **Implement Robust Error Handling:**  
  Prepare for scenarios where no agents match the criteria. This may involve default routing strategies or alert mechanisms.

- **Test Thoroughly:**  
  Regularly test the module under various conditions to ensure that the scoring and routing logic remains effective as system dynamics change.

---

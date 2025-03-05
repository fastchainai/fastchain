# Context Manager

**File:** `src/context/context_manager.py`

## Overview

The Context Manager is a shared module that provides functions for managing context in a multi-agent system. It maintains state across multi-step processes, ensuring continuity during interactions that span multiple agents or require historical context. This module is critical for preserving session data, such as conversation history or processing states, which agents can reference to deliver contextually relevant responses.

## Key Responsibilities

- **State Persistence:**  
  Store and retrieve context data for each session, ensuring that multi-step processes have access to necessary historical data.

- **Shared Context:**  
  Allow multiple agents to access and update common context data, facilitating collaboration across task boundaries.

- **Session Management:**  
  Support the creation, updating, merging, and deletion of session-specific context, isolating data between concurrent sessions.

- **Data Consistency:**  
  Maintain consistent and thread-safe access to context data, even under concurrent operations.

## Optional Enhancements and Features

This enhanced implementation includes several optional features controlled by Dynaconf configuration settings or feature flags:

1. **Partial Updates:**  
   - **Description:** Update specific parts of a complex context object without replacing the entire structure.  
   - **Implementation:** A recursive update function merges new data into the existing context.

2. **Redis-Based Caching:**  
   - **Description:** Optionally store context data in Redis rather than in-memory. This allows for distributed, persistent context management across multiple nodes.
   - **Configuration Flag:** `USE_REDIS_CACHING`

3. **Time-Based Expiration:**  
   - **Description:** Automatically expire sessions after a configurable timeout period.  
   - **Configuration Flags:** `TIME_BASED_EXPIRATION` and `SESSION_EXPIRATION_SECONDS`

4. **Garbage Collection:**  
   - **Description:** A background thread periodically cleans up expired sessions from the in-memory store.
   - **Configuration Flag:** `GARBAGE_COLLECTION`

5. **Asynchronous Operations:**  
   - **Description:** Provide async versions of the context operations to improve scalability in high-concurrency environments.
   - **Configuration Flag:** `ASYNC_OPERATIONS`

6. **Event Emission:**  
   - **Description:** Emit events on context creation, update, and deletion. This allows integration with external monitoring or workflow systems.
   - **Configuration Flag:** `EVENT_EMISSION`

## Architecture and Components

The Context Manager uses one of two storage mechanisms based on configuration:
- **In-Memory Storage:** A Python dictionary (with thread locks) is used to store session context.
- **Redis Storage:** If enabled, context data is stored in Redis using hashes.

### Core Functions

- **Session Creation:**  
  - `create_session(session_id: str) -> None`  
  Initializes a new context session, adding a `_timestamp` to track last update time.

- **Set Context:**  
  - `set_context(session_id: str, key: str, value: Any) -> None`  
  Adds or updates a specific key-value pair in the session context. Updates the session’s timestamp.

- **Partial Update:**  
  - `update_partial_context(session_id: str, partial_context: Dict[str, Any]) -> None`  
  Merges new data into the existing context using a recursive update, preserving unchanged fields.

- **Get Context:**  
  - `get_context(session_id: str) -> Dict[str, Any]`  
  Retrieves the entire context for a session, returning an empty dictionary if the session does not exist.

- **Delete Context:**  
  - `delete_context(session_id: str) -> None`  
  Removes the session’s context from storage.

- **Asynchronous Versions:**  
  Async counterparts are provided for key operations (create, set, get, delete, update partial) when `ASYNC_OPERATIONS` is enabled.

- **Event Emission:**  
  - The manager supports registering event listener callbacks that are called on session events (creation, update, deletion, etc.).

- **Garbage Collection:**  
  - A background thread is launched (if enabled) to periodically remove expired sessions based on a configurable timeout.

## Example Usage

```python
# Example usage for testing purposes
if __name__ == "__main__":
    cm = ContextManager()

    session = "session_001"
    cm.create_session(session)
    cm.set_context(session, "user_query", "How do I book a flight?")
    cm.set_context(session, "agent", "chat_agent")
    
    print("Initial Context:", cm.get_context(session))
    
    # Perform a partial update to add new details without overwriting existing data.
    partial_update = {"intent": "booking", "details": {"class": "economy", "flexible": True}}
    cm.update_partial_context(session, partial_update)
    
    print("After Partial Update:", cm.get_context(session))
    
    # Demonstrate asynchronous operation if enabled
    if cm.async_enabled:
        import asyncio
        async def async_demo():
            await cm.async_set_context(session, "async_key", "async_value")
            ctx = await cm.async_get_context(session)
            print("Async Context:", ctx)
        asyncio.run(async_demo())
    
    # Optionally, delete the session context once processing is complete
    cm.delete_context(session)
    print("Final Context:", cm.get_context(session))
```

## Best Practices

- **Session Identification:**  
  Use unique and descriptive session IDs to prevent conflicts.

- **Regular Cleanup:**  
  Enable time-based expiration and garbage collection to avoid memory bloat from stale sessions.

- **Consistent Event Handling:**  
  Register event listeners to log or react to context changes, enhancing observability and integration with external systems.

- **Distributed Considerations:**  
  When scaling across multiple nodes, consider enabling Redis-based caching for shared context access.

- **Concurrency:**  
  Use asynchronous operations and proper locking to ensure that context updates are consistent and performant under high load.

---
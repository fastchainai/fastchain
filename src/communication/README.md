# Communication Module

This module provides standardized utilities for both inter-agent and external communication in the multi-agent system.

## Features

- **Standardized Message Protocol**: Ensures all communications follow a consistent format
- **Robust Error Handling**: Includes retry mechanisms and fallback strategies
- **Telemetry Integration**: Built-in logging and performance tracking
- **Extensible Design**: Easy to extend for new protocols and integrations

## Usage

```python
from src.communication import (
    Message,
    MessageType,
    MessagePriority,
    agent_handler,
    external_handler
)

# Create a message
message = Message(
    message_id="unique-id",
    message_type=MessageType.QUERY,
    sender="agent_a",
    recipient="agent_b",
    content={"query": "process_data"}
)

# Send message using agent handler
response = await agent_handler.send_message(message)

# Handle external communication
external_response = await external_handler.send_message(message)
```

## Message Types

- `COMMAND`: For action requests
- `QUERY`: For information requests
- `RESPONSE`: For replies
- `EVENT`: For notifications
- `ERROR`: For error reporting

## Priority Levels

- `LOW`: Non-urgent communications
- `MEDIUM`: Standard priority (default)
- `HIGH`: Time-sensitive messages
- `CRITICAL`: Urgent, immediate handling required

## Error Handling

The module includes automatic retry mechanisms with exponential backoff for failed communications:

- Configurable retry attempts
- Exponential backoff strategy
- Timeout handling
- Detailed error reporting

## Telemetry and Observability

Integrated with OpenTelemetry for comprehensive monitoring:

- Distributed tracing
- Performance metrics
- Error tracking
- Resource utilization monitoring

## Security Features

- Message validation using Pydantic models
- Secure message routing
- Error isolation
- Rate limiting support

## Extending the Module

Create custom handlers by extending the base `MessageHandler` class:

```python
class CustomHandler(MessageHandler):
    async def _send(self, message: Message) -> Message:
        # Implement custom sending logic
        pass
```

## Best Practices

1. Always specify message priorities appropriately
2. Handle timeouts explicitly
3. Monitor telemetry data
4. Implement proper error handling
5. Use correlation IDs for related messages

## Integration with External Systems

The `ExternalCommunicationHandler` provides a foundation for external system integration:

- API adaptors
- Protocol translation
- Security middleware
- Rate limiting

For more details, refer to the API documentation and integration guides.
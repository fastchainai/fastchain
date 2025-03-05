"""Communication module for standardized inter-agent and external communication."""
from .communication import (
    Message,
    MessageType,
    MessagePriority,
    CommunicationError,
    AgentCommunicationHandler,
    ExternalCommunicationHandler,
    agent_handler,
    external_handler
)

__all__ = [
    'Message',
    'MessageType',
    'MessagePriority',
    'CommunicationError',
    'AgentCommunicationHandler',
    'ExternalCommunicationHandler',
    'agent_handler',
    'external_handler'
]

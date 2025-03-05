"""Standardized communication utilities for inter-agent and external communication."""
import asyncio
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from src.utils.logging.logger import Logging
from src.utils.tracing.tracer import Tracing
from src.utils.metrics.metrics import MetricsCollector
from src.config.config import settings

# Initialize shared utilities
logger = Logging(__name__, level=settings.get("DEFAULT_LOG_LEVEL", "INFO"))
tracer = Tracing(service_name="communication")
metrics = MetricsCollector()

class MessageType(str, Enum):
    """Enumeration of supported message types."""
    COMMAND = "command"
    QUERY = "query"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"

class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Message(BaseModel):
    """Standardized message format for all communications."""
    message_id: str = Field(..., description="Unique identifier for the message")
    message_type: MessageType
    priority: MessagePriority = Field(default=MessagePriority.MEDIUM)
    sender: str = Field(..., description="Identifier of the sending agent/system")
    recipient: str = Field(..., description="Identifier of the intended recipient")
    content: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = Field(None, description="ID for tracking related messages")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RetryConfig(BaseModel):
    """Configuration for retry behavior."""
    max_retries: int = settings.get("TASK_MAX_RETRIES", 3)
    base_delay: float = settings.get("TASK_RETRY_DELAY", 1.0)  # seconds
    max_delay: float = settings.get("TASK_MAX_RETRY_DELAY", 10.0)  # seconds
    timeout: float = settings.get("TASK_DEFAULT_TIMEOUT", 30.0)    # seconds

class CommunicationError(Exception):
    """Base exception for communication-related errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}

class MessageHandler:
    """Base handler for processing messages."""
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.retry_config = retry_config or RetryConfig()

    async def send_message(
        self,
        message: Message,
        timeout: Optional[float] = None
    ) -> Message:
        """
        Send a message with retry logic and telemetry tracking.

        Args:
            message: The message to send
            timeout: Optional timeout override

        Returns:
            Message: Response message

        Raises:
            CommunicationError: If sending fails after retries or times out
        """
        span = tracer.start_trace("send_message")
        start_time = time.time()
        span.set_attribute("start_time", start_time)
        span.set_attribute("message.id", message.message_id)
        span.set_attribute("message.type", message.message_type)

        timeout = timeout or self.retry_config.timeout
        attempt = 0

        try:
            while True:
                try:
                    logger.debug(
                        "Sending message",
                        extra={
                            "message_id": message.message_id,
                            "attempt": attempt + 1
                        }
                    )

                    # Track message attempt metrics
                    metrics.increment("message_attempts_total", 
                                   labels={"type": message.message_type})

                    # Implement actual message sending logic here with timeout
                    try:
                        response = await asyncio.wait_for(
                            self._send(message),
                            timeout=timeout
                        )

                        # Track successful message
                        metrics.increment("messages_sent_total",
                                       labels={"type": message.message_type,
                                              "status": "success"})

                        span.set_status("ok")
                        return response

                    except asyncio.TimeoutError as e:
                        metrics.increment("message_timeouts_total",
                                       labels={"type": message.message_type})

                        error_details = {
                            "message_id": message.message_id,
                            "attempt": attempt + 1,
                            "timeout": timeout,
                            "error": "Operation timed out"
                        }
                        logger.error(
                            "Message send timed out",
                            extra=error_details
                        )
                        raise CommunicationError(
                            "Operation timed out",
                            error_details
                        ) from e

                except Exception as e:
                    attempt += 1
                    if attempt >= self.retry_config.max_retries:
                        metrics.increment("message_failures_total",
                                       labels={"type": message.message_type,
                                              "error": type(e).__name__})

                        error_details = {
                            "message_id": message.message_id,
                            "attempt": attempt,
                            "error": str(e)
                        }
                        logger.error(
                            "Failed to send message after retries",
                            extra=error_details
                        )
                        span.set_status("error", description="Failed to send message after retries")

                        if isinstance(e, CommunicationError):
                            raise
                        raise CommunicationError(
                            "Failed to send message after retries",
                            error_details
                        ) from e

                    delay = min(
                        self.retry_config.base_delay * (2 ** attempt),
                        self.retry_config.max_delay
                    )
                    logger.warning(
                        "Retrying message send",
                        extra={
                            "message_id": message.message_id,
                            "attempt": attempt,
                            "delay": delay
                        }
                    )
                    await asyncio.sleep(delay)

        finally:
            # Calculate and record duration metrics
            duration = time.time() - start_time
            span.set_attribute("duration_seconds", duration)
            metrics.observe("message_duration_seconds",
                          duration,
                          labels={"type": message.message_type})
            tracer.end_trace(span)

    async def _send(self, message: Message) -> Message:
        """
        Internal method to be implemented by specific handlers.

        Args:
            message: The message to send

        Returns:
            Message: Response message
        """
        raise NotImplementedError("Specific handlers must implement _send method")

class AgentCommunicationHandler(MessageHandler):
    """Handler for inter-agent communication."""
    async def _send(self, message: Message) -> Message:
        # Here we would implement the actual inter-agent communication logic
        # For now, we'll just echo back a response
        response_content = {
            "status": "received",
            "original_message_id": message.message_id
        }

        return Message(
            message_id=f"response-{message.message_id}",
            message_type=MessageType.RESPONSE,
            sender=message.recipient,
            recipient=message.sender,
            content=response_content,
            correlation_id=message.message_id
        )

class ExternalCommunicationHandler(MessageHandler):
    """Handler for external system communication."""
    async def _send(self, message: Message) -> Message:
        # Here we would implement external API calls or other external communication
        # For now, we'll just echo back a response
        response_content = {
            "status": "received",
            "original_message_id": message.message_id
        }

        return Message(
            message_id=f"response-{message.message_id}",
            message_type=MessageType.RESPONSE,
            sender=message.recipient,
            recipient=message.sender,
            content=response_content,
            correlation_id=message.message_id
        )

# Global communication handlers
agent_handler = AgentCommunicationHandler()
external_handler = ExternalCommunicationHandler()
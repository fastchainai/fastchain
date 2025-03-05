"""Unit tests for message handlers in communication module."""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from src.communication.communication import (
    Message,
    MessageType,
    MessagePriority,
    MessageHandler,
    AgentCommunicationHandler,
    ExternalCommunicationHandler,
    CommunicationError,
    RetryConfig
)

@pytest.fixture
def mock_metrics():
    """Fixture for mocked metrics collector."""
    with patch('src.communication.communication.metrics') as mock:
        yield mock

@pytest.fixture
def mock_tracer():
    """Fixture for mocked tracer."""
    with patch('src.communication.communication.tracer') as mock:
        # Mock span context manager
        mock_span = Mock()
        mock.start_trace.return_value = mock_span
        yield mock

@pytest.fixture
def mock_logger():
    """Fixture for mocked logger."""
    with patch('src.communication.communication.logger') as mock:
        yield mock

class TestMessageHandler:
    """Test cases for base MessageHandler class."""

    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_metrics, mock_tracer, mock_logger):
        """Test successful message sending."""
        class TestHandler(MessageHandler):
            async def _send(self, message):
                return Message(
                    message_id="response-123",
                    message_type=MessageType.RESPONSE,
                    sender="target",
                    recipient="sender",
                    content={"status": "success"}
                )

        handler = TestHandler()
        message = Message(
            message_id="test-123",
            message_type=MessageType.COMMAND,
            sender="sender",
            recipient="target",
            content={"command": "test"}
        )

        response = await handler.send_message(message)

        assert response.message_id == "response-123"
        assert response.message_type == MessageType.RESPONSE
        mock_metrics.increment.assert_called_with(
            "message_attempts_total",
            labels={"type": message.message_type}
        )
        mock_tracer.start_trace.assert_called_once()
        mock_tracer.end_trace.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, mock_metrics, mock_tracer, mock_logger):
        """Test retry behavior on temporary failures."""
        class TemporaryFailHandler(MessageHandler):
            def __init__(self):
                super().__init__(RetryConfig(max_retries=2, base_delay=0.1))
                self.attempts = 0

            async def _send(self, message):
                self.attempts += 1
                if self.attempts < 2:
                    raise Exception("Temporary failure")
                return Message(
                    message_id="response-123",
                    message_type=MessageType.RESPONSE,
                    sender="target",
                    recipient="sender",
                    content={"status": "success"}
                )

        handler = TemporaryFailHandler()
        message = Message(
            message_id="test-123",
            message_type=MessageType.COMMAND,
            sender="sender",
            recipient="target",
            content={"command": "test"}
        )

        response = await handler.send_message(message)

        assert handler.attempts == 2
        assert response.message_id == "response-123"
        mock_metrics.increment.assert_called()
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_metrics, mock_tracer, mock_logger):
        """Test behavior when max retries are exceeded."""
        class AlwaysFailHandler(MessageHandler):
            async def _send(self, message):
                raise Exception("Permanent failure")

        handler = AlwaysFailHandler()
        message = Message(
            message_id="test-123",
            message_type=MessageType.COMMAND,
            sender="sender",
            recipient="target",
            content={"command": "test"}
        )

        with pytest.raises(CommunicationError) as exc_info:
            await handler.send_message(message)

        assert "Failed to send message after retries" in str(exc_info.value)
        mock_metrics.increment.assert_called_with(
            "message_failures_total",
            labels={"type": message.message_type, "error": "Exception"}
        )
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_metrics, mock_tracer, mock_logger):
        """Test handling of timeouts."""
        class SlowHandler(MessageHandler):
            async def _send(self, message):
                await asyncio.sleep(0.5)  # Simulate slow operation
                return Message(
                    message_id="response-123",
                    message_type=MessageType.RESPONSE,
                    sender="target",
                    recipient="sender",
                    content={"status": "success"}
                )

        handler = SlowHandler(RetryConfig(timeout=0.1))
        message = Message(
            message_id="test-123",
            message_type=MessageType.COMMAND,
            sender="sender",
            recipient="target",
            content={"command": "test"}
        )

        with pytest.raises(CommunicationError) as exc_info:
            await handler.send_message(message)

        assert "Operation timed out" in str(exc_info.value)
        mock_metrics.increment.assert_called_with(
            "message_timeouts_total",
            labels={"type": message.message_type}
        )

class TestAgentCommunicationHandler:
    """Test cases for AgentCommunicationHandler."""

    @pytest.mark.asyncio
    async def test_agent_communication(self, mock_metrics, mock_tracer):
        """Test basic agent-to-agent communication."""
        handler = AgentCommunicationHandler()
        message = Message(
            message_id="test-123",
            message_type=MessageType.COMMAND,
            sender="agent_a",
            recipient="agent_b",
            content={"command": "test"}
        )

        response = await handler.send_message(message)

        assert response.message_type == MessageType.RESPONSE
        assert response.sender == message.recipient
        assert response.recipient == message.sender
        assert response.correlation_id == message.message_id
        assert "status" in response.content
        assert response.content["original_message_id"] == message.message_id

class TestExternalCommunicationHandler:
    """Test cases for ExternalCommunicationHandler."""

    @pytest.mark.asyncio
    async def test_external_communication(self, mock_metrics, mock_tracer):
        """Test communication with external systems."""
        handler = ExternalCommunicationHandler()
        message = Message(
            message_id="test-123",
            message_type=MessageType.QUERY,
            sender="internal_service",
            recipient="external_api",
            content={"query": "test"}
        )

        response = await handler.send_message(message)

        assert response.message_type == MessageType.RESPONSE
        assert response.sender == message.recipient
        assert response.recipient == message.sender
        assert response.correlation_id == message.message_id
        assert "status" in response.content
        assert response.content["original_message_id"] == message.message_id

    @pytest.mark.asyncio
    async def test_external_error_handling(self, mock_metrics, mock_tracer):
        """Test handling of external system errors."""
        handler = ExternalCommunicationHandler()
        message = Message(
            message_id="test-123",
            message_type=MessageType.COMMAND,
            sender="internal_service",
            recipient="external_api",
            content={"command": "invalid"}
        )

        # Mock the _send method to simulate an external error
        async def mock_send(*args, **kwargs):
            raise CommunicationError("External system error", {"status": 500})

        with patch.object(handler, '_send', side_effect=mock_send):
            with pytest.raises(CommunicationError) as exc_info:
                await handler.send_message(message)

            assert "External system error" in str(exc_info.value)
            mock_metrics.increment.assert_called_with(
                "message_failures_total",
                labels={"type": message.message_type, "error": "CommunicationError"}
            )
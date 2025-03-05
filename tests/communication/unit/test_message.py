"""Unit tests for Message model in communication module."""
import pytest
from datetime import datetime
from src.communication.communication import Message, MessageType, MessagePriority

def test_message_creation():
    """Test creating a message with required fields."""
    message = Message(
        message_id="test-123",
        message_type=MessageType.COMMAND,
        sender="test_agent",
        recipient="target_agent",
        content={"command": "test"}
    )

    assert message.message_id == "test-123"
    assert message.message_type == MessageType.COMMAND
    assert message.sender == "test_agent"
    assert message.recipient == "target_agent"
    assert message.content == {"command": "test"}
    assert message.priority == MessagePriority.MEDIUM  # Default priority
    assert isinstance(message.timestamp, datetime)
    assert message.correlation_id is None
    assert message.metadata == {}

def test_message_with_all_fields():
    """Test creating a message with all optional fields."""
    timestamp = datetime.utcnow()
    message = Message(
        message_id="test-456",
        message_type=MessageType.QUERY,
        sender="agent_a",
        recipient="agent_b",
        content={"query": "data"},
        priority=MessagePriority.HIGH,
        timestamp=timestamp,
        correlation_id="corr-123",
        metadata={"source": "test"}
    )

    assert message.message_id == "test-456"
    assert message.message_type == MessageType.QUERY
    assert message.priority == MessagePriority.HIGH
    assert message.timestamp == timestamp
    assert message.correlation_id == "corr-123"
    assert message.metadata == {"source": "test"}

def test_message_type_validation():
    """Test that message type validation works."""
    with pytest.raises(ValueError):
        Message(
            message_id="test-789",
            message_type="invalid_type",  # Invalid message type
            sender="agent_a",
            recipient="agent_b",
            content={}
        )

def test_message_priority_validation():
    """Test that priority validation works."""
    with pytest.raises(ValueError):
        Message(
            message_id="test-789",
            message_type=MessageType.COMMAND,
            sender="agent_a",
            recipient="agent_b",
            content={},
            priority="invalid_priority"  # Invalid priority
        )

def test_empty_content_validation():
    """Test that empty content is allowed but must be a dict."""
    message = Message(
        message_id="test-789",
        message_type=MessageType.EVENT,
        sender="agent_a",
        recipient="agent_b",
        content={}
    )
    assert message.content == {}

    with pytest.raises(ValueError):
        Message(
            message_id="test-789",
            message_type=MessageType.EVENT,
            sender="agent_a",
            recipient="agent_b",
            content=None  # Invalid content type
        )

def test_message_serialization():
    """Test message serialization and deserialization."""
    original = Message(
        message_id="test-123",
        message_type=MessageType.COMMAND,
        sender="agent_a",
        recipient="agent_b",
        content={"data": "test"},
        metadata={"source": "test"}
    )

    # Test dict conversion
    message_dict = original.dict()
    assert isinstance(message_dict, dict)
    assert message_dict["message_id"] == original.message_id

    # Test JSON serialization
    message_json = original.json()
    assert isinstance(message_json, str)

    # Test model validation
    reconstructed = Message.parse_raw(message_json)
    assert reconstructed.message_id == original.message_id
    assert reconstructed.message_type == original.message_type
    assert reconstructed.content == original.content

def test_message_immutability():
    """Test that message fields cannot be modified after creation."""
    message = Message(
        message_id="test-123",
        message_type=MessageType.COMMAND,
        sender="agent_a",
        recipient="agent_b",
        content={"command": "test"}
    )

    with pytest.raises(Exception):  # Type of exception depends on Pydantic version
        message.message_id = "new-id"

def test_message_hash_and_equality():
    """Test message hashing and equality comparison."""
    msg1 = Message(
        message_id="test-123",
        message_type=MessageType.COMMAND,
        sender="agent_a",
        recipient="agent_b",
        content={"command": "test"}
    )

    msg2 = Message(
        message_id="test-123",
        message_type=MessageType.COMMAND,
        sender="agent_a",
        recipient="agent_b",
        content={"command": "test"}
    )

    # Same content should result in equal messages
    assert msg1 == msg2
    assert hash(msg1) == hash(msg2)

    # Different content should result in different messages
    msg3 = Message(
        message_id="test-456",
        message_type=MessageType.COMMAND,
        sender="agent_a",
        recipient="agent_b",
        content={"command": "test"}
    )
    assert msg1 != msg3
    assert hash(msg1) != hash(msg3)
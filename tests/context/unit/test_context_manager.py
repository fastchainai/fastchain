"""Unit tests for the Context Manager module."""
import pytest
from unittest.mock import Mock, patch
from src.context.context_manager import ContextManager

@pytest.fixture
def context_manager():
    """Create a ContextManager instance for testing."""
    return ContextManager()

@pytest.fixture
def sample_context():
    """Create a sample context dictionary for testing."""
    return {
        "user_id": "test_user",
        "session_id": "test_session",
        "conversation_history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ],
        "metadata": {
            "language": "en",
            "timezone": "UTC"
        }
    }

def test_context_manager_initialization(context_manager):
    """Test ContextManager initialization."""
    assert context_manager.contexts == {}
    assert context_manager.max_context_size == 1000
    assert context_manager.cleanup_threshold == 0.8

def test_create_context(context_manager):
    """Test creating a new context."""
    context_id = context_manager.create_context("test_user")
    assert context_id in context_manager.contexts
    assert "user_id" in context_manager.contexts[context_id]
    assert "created_at" in context_manager.contexts[context_id]
    assert "last_updated" in context_manager.contexts[context_id]

def test_get_context(context_manager, sample_context):
    """Test retrieving a context."""
    context_id = context_manager.create_context("test_user")
    context_manager.contexts[context_id].update(sample_context)
    
    retrieved_context = context_manager.get_context(context_id)
    assert retrieved_context == context_manager.contexts[context_id]

def test_get_nonexistent_context(context_manager):
    """Test attempting to retrieve a nonexistent context."""
    with pytest.raises(KeyError) as exc:
        context_manager.get_context("nonexistent_id")
    assert "Context not found" in str(exc.value)

def test_update_context(context_manager):
    """Test updating an existing context."""
    context_id = context_manager.create_context("test_user")
    update_data = {"new_key": "new_value"}
    
    context_manager.update_context(context_id, update_data)
    assert context_manager.contexts[context_id]["new_key"] == "new_value"
    assert "last_updated" in context_manager.contexts[context_id]

def test_update_nonexistent_context(context_manager):
    """Test attempting to update a nonexistent context."""
    with pytest.raises(KeyError) as exc:
        context_manager.update_context("nonexistent_id", {})
    assert "Context not found" in str(exc.value)

def test_delete_context(context_manager):
    """Test deleting a context."""
    context_id = context_manager.create_context("test_user")
    context_manager.delete_context(context_id)
    assert context_id not in context_manager.contexts

def test_delete_nonexistent_context(context_manager):
    """Test attempting to delete a nonexistent context."""
    with pytest.raises(KeyError) as exc:
        context_manager.delete_context("nonexistent_id")
    assert "Context not found" in str(exc.value)

def test_cleanup_old_contexts(context_manager):
    """Test cleaning up old contexts."""
    # Create multiple contexts
    context_ids = [
        context_manager.create_context(f"user_{i}")
        for i in range(context_manager.max_context_size + 10)
    ]
    
    # Verify cleanup occurred
    assert len(context_manager.contexts) <= context_manager.max_context_size
    # Verify most recent contexts are retained
    assert context_ids[-1] in context_manager.contexts

def test_context_size_limit(context_manager):
    """Test context size limit enforcement."""
    context_id = context_manager.create_context("test_user")
    large_data = {"data": "x" * (context_manager.max_context_size + 1)}
    
    with pytest.raises(ValueError) as exc:
        context_manager.update_context(context_id, large_data)
    assert "Context size exceeds maximum limit" in str(exc.value)

def test_get_context_history(context_manager, sample_context):
    """Test retrieving conversation history from context."""
    context_id = context_manager.create_context("test_user")
    context_manager.contexts[context_id].update(sample_context)
    
    history = context_manager.get_context_history(context_id)
    assert history == sample_context["conversation_history"]

def test_add_to_history(context_manager):
    """Test adding messages to conversation history."""
    context_id = context_manager.create_context("test_user")
    message = {"role": "user", "content": "Hello"}
    
    context_manager.add_to_history(context_id, message)
    history = context_manager.get_context_history(context_id)
    assert message in history

@pytest.mark.parametrize("metadata", [
    {"language": "en"},
    {"timezone": "UTC"},
    {"custom_key": "custom_value"}
])
def test_update_context_metadata(context_manager, metadata):
    """Test updating context metadata with various values."""
    context_id = context_manager.create_context("test_user")
    context_manager.update_context_metadata(context_id, metadata)
    
    context = context_manager.get_context(context_id)
    assert all(item in context["metadata"].items() for item in metadata.items())

def test_context_expiration(context_manager):
    """Test context expiration functionality."""
    with patch('time.time', return_value=1000):
        context_id = context_manager.create_context("test_user")
    
    with patch('time.time', return_value=1000 + context_manager.context_ttl + 1):
        with pytest.raises(ValueError) as exc:
            context_manager.get_context(context_id)
        assert "Context has expired" in str(exc.value)

def test_bulk_context_operations(context_manager):
    """Test bulk operations on contexts."""
    # Create multiple contexts
    context_ids = [
        context_manager.create_context(f"user_{i}")
        for i in range(5)
    ]
    
    # Bulk update
    update_data = {"shared_key": "shared_value"}
    for context_id in context_ids:
        context_manager.update_context(context_id, update_data)
    
    # Verify updates
    for context_id in context_ids:
        context = context_manager.get_context(context_id)
        assert context["shared_key"] == "shared_value"

def test_context_isolation(context_manager):
    """Test that contexts are properly isolated from each other."""
    context_id1 = context_manager.create_context("user_1")
    context_id2 = context_manager.create_context("user_2")
    
    context_manager.update_context(context_id1, {"key": "value1"})
    context_manager.update_context(context_id2, {"key": "value2"})
    
    context1 = context_manager.get_context(context_id1)
    context2 = context_manager.get_context(context_id2)
    
    assert context1["key"] == "value1"
    assert context2["key"] == "value2"

"""Unit tests for the TaskRouter component."""
import pytest
from unittest.mock import Mock, patch
from src.utils.task_router import TaskRouter
from src.tools import ToolRegistry, Tool
from src.tools.base import ToolContext

@pytest.fixture
def mock_tool():
    """Create a mock tool for testing."""
    mock = Mock(spec=Tool)
    mock.name = "test_tool"
    mock.version = "1.0"
    mock.get_metadata.return_value = {
        "name": "test_tool",
        "version": "1.0",
        "capabilities": ["test"]
    }
    return mock

@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry."""
    mock = Mock(spec=ToolRegistry)
    mock.get_all_tools.return_value = []
    return mock

class TestTaskRouter:
    """Test suite for TaskRouter class."""

    def test_initialization_with_registry(self, mock_tool_registry):
        """Test TaskRouter initialization with provided registry."""
        router = TaskRouter(tool_registry=mock_tool_registry)
        assert router.tool_registry == mock_tool_registry
        mock_tool_registry.get_all_tools.assert_called_once()

    def test_initialization_creates_registry(self):
        """Test TaskRouter creates new registry when none provided."""
        with patch('src.utils.task_router.ToolRegistry') as mock_registry_class:
            mock_registry = Mock()
            mock_registry_class.return_value = mock_registry
            router = TaskRouter()
            assert router.tool_registry == mock_registry
            mock_registry_class.assert_called_once()

    def test_register_default_tools(self):
        """Test registration of default tools."""
        with patch('src.utils.task_router.SearchTool') as mock_search_tool:
            router = TaskRouter()
            router.tool_registry.register.assert_called_with(mock_search_tool)

    def test_route_task_successful(self, mock_tool_registry, mock_tool):
        """Test successful task routing."""
        mock_tool_registry.select_tool.return_value = mock_tool
        mock_tool.execute.return_value = "Success"

        router = TaskRouter(tool_registry=mock_tool_registry)
        result = router.route_task(
            intent="test_intent",
            entities={"entity1": ["value1"]},
            metadata={"confidence": 0.8}
        )

        assert "Success" in result
        mock_tool_registry.select_tool.assert_called_once()
        mock_tool.execute.assert_called_once()

    def test_route_task_no_tool_found(self, mock_tool_registry):
        """Test behavior when no suitable tool is found."""
        mock_tool_registry.select_tool.return_value = None

        router = TaskRouter(tool_registry=mock_tool_registry)
        result = router.route_task(
            intent="unknown_intent",
            entities={},
            metadata={"confidence": 0.5}
        )

        assert "Unable to find appropriate tool" in result
        mock_tool_registry.select_tool.assert_called_once()

    def test_route_task_execution_error(self, mock_tool_registry, mock_tool):
        """Test handling of tool execution errors."""
        from src.tools import ToolExecutionError

        mock_tool_registry.select_tool.return_value = mock_tool
        mock_tool.execute.side_effect = ToolExecutionError("Test error")

        router = TaskRouter(tool_registry=mock_tool_registry)
        result = router.route_task(
            intent="test_intent",
            entities={},
            metadata={"confidence": 0.8}
        )

        assert "Error executing task" in result
        assert "Test error" in result
        mock_tool.execute.assert_called_once()

    def test_route_task_with_context(self, mock_tool_registry, mock_tool):
        """Test task routing with full context information."""
        mock_tool_registry.select_tool.return_value = mock_tool

        router = TaskRouter(tool_registry=mock_tool_registry)
        metadata = {
            "intent_confidence": 0.9,
            "query": "test query",
            "source": "test"
        }

        router.route_task(
            intent="test_intent",
            entities={"entity1": ["value1"]},
            metadata=metadata
        )

        # Verify context creation
        mock_tool_registry.select_tool.assert_called_with(
            context={
                'intent': "test_intent",
                'entities': {"entity1": ["value1"]},
                'metadata': metadata,
                'confidence': 0.9
            },
            min_confidence=0.1
        )

    def test_route_task_general_error(self, mock_tool_registry):
        """Test handling of general errors during routing."""
        mock_tool_registry.select_tool.side_effect = Exception("Unexpected error")

        router = TaskRouter(tool_registry=mock_tool_registry)
        result = router.route_task(
            intent="test_intent",
            entities={},
            metadata={}
        )

        assert "Error routing task" in result
        assert "Unexpected error" in result

    def test_route_task_with_retry(self, mock_tool_registry, mock_tool):
        """Test task routing with retry on temporary failure."""
        mock_tool_registry.select_tool.return_value = mock_tool
        mock_tool.execute.side_effect = [
            Exception("Temporary error"),
            "Success on retry"
        ]

        router = TaskRouter(tool_registry=mock_tool_registry)
        result = router.route_task(
            intent="test_intent",
            entities={},
            metadata={"should_retry": True}
        )

        assert "Success on retry" in result
        assert mock_tool.execute.call_count == 2

    def test_route_task_with_metrics(self, mock_tool_registry, mock_tool):
        """Test that routing updates tool metrics."""
        mock_tool_registry.select_tool.return_value = mock_tool
        mock_tool.execute.return_value = "Success"

        router = TaskRouter(tool_registry=mock_tool_registry)
        router.route_task(
            intent="test_intent",
            entities={},
            metadata={"track_metrics": True}
        )

        # Verify metrics were updated
        tool_metrics = mock_tool.get_metadata()["metrics"]
        assert "execution_time" in tool_metrics
        assert "success_rate" in tool_metrics
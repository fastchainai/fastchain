"""Unit tests for the base tools module."""
import pytest
from datetime import datetime
from typing import Dict, Any, List
from src.tools.base import Tool, ToolMetrics, ToolContext, ToolResult, ToolRegistry
from src.tools.exceptions import ToolExecutionError, ToolValidationError

class MockTool(Tool):
    """Mock implementation of Tool for testing."""
    name = "mock_tool"
    description = "A mock tool for testing"
    required_params = ["param1"]
    version = "1.0.0"
    compatible_versions = ["0.9.0"]

    def can_handle(self, context: ToolContext) -> float:
        """Mock implementation of can_handle."""
        return 0.8 if context.intent == "test_intent" else 0.0

    def _execute_impl(self, params: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        """Mock implementation of execute."""
        if not self.validate_params(params):
            raise ToolValidationError("Invalid parameters")

        if params.get("should_fail"):
            raise ToolExecutionError("Execution failed as requested")

        return {"result": "success", "param1": params["param1"]}

@pytest.fixture
def tool_context() -> ToolContext:
    """Create a ToolContext instance for testing."""
    return ToolContext(
        intent="test_intent",
        confidence=0.9,
        entities={"entity1": ["value1"]},
        metadata={"test": "data"},
        chain_context={"previous": "result"}
    )

@pytest.fixture
def mock_tool() -> MockTool:
    """Create a MockTool instance for testing."""
    return MockTool()

@pytest.fixture
def tool_registry() -> ToolRegistry:
    """Create a ToolRegistry instance for testing."""
    return ToolRegistry()

class TestToolMetrics:
    """Test suite for ToolMetrics."""

    def test_initialization(self):
        """Test ToolMetrics initialization with default values."""
        metrics = ToolMetrics()
        assert metrics.execution_time == 0.0
        assert metrics.success_rate == 0.0
        assert metrics.last_execution is None
        assert metrics.total_executions == 0
        assert metrics.failed_executions == 0

    def test_custom_values(self):
        """Test ToolMetrics initialization with custom values."""
        now = datetime.now()
        metrics = ToolMetrics(
            execution_time=1.5,
            success_rate=0.75,
            last_execution=now,
            total_executions=10,
            failed_executions=2
        )
        assert metrics.execution_time == 1.5
        assert metrics.success_rate == 0.75
        assert metrics.last_execution == now
        assert metrics.total_executions == 10
        assert metrics.failed_executions == 2

class TestToolContext:
    """Test suite for ToolContext."""

    def test_initialization(self, tool_context):
        """Test ToolContext initialization."""
        assert tool_context.intent == "test_intent"
        assert tool_context.confidence == 0.9
        assert tool_context.entities == {"entity1": ["value1"]}
        assert tool_context.metadata == {"test": "data"}
        assert tool_context.chain_context == {"previous": "result"}

class TestToolResult:
    """Test suite for ToolResult."""

    def test_successful_result(self):
        """Test ToolResult for successful execution."""
        result = ToolResult(
            success=True,
            data={"output": "test"},
            next_tools=["tool1", "tool2"]
        )
        assert result.success is True
        assert result.data == {"output": "test"}
        assert result.next_tools == ["tool1", "tool2"]
        assert result.error_message is None

    def test_failed_result(self):
        """Test ToolResult for failed execution."""
        result = ToolResult(
            success=False,
            data={},
            error_message="Test error"
        )
        assert result.success is False
        assert result.data == {}
        assert result.next_tools == []
        assert result.error_message == "Test error"

class TestTool:
    """Test suite for Tool base class."""

    def test_initialization(self, mock_tool):
        """Test Tool initialization."""
        assert mock_tool.name == "mock_tool"
        assert mock_tool.description == "A mock tool for testing"
        assert mock_tool.required_params == ["param1"]
        assert isinstance(mock_tool.metrics, ToolMetrics)

    def test_initialization_without_name(self):
        """Test Tool initialization without a name."""
        class InvalidTool(Tool):
            name = ""

            def can_handle(self, context):
                return 0.0

            def _execute_impl(self, params, context):
                return {}

        with pytest.raises(ValueError):
            InvalidTool()

    def test_execute_success(self, mock_tool, tool_context):
        """Test successful tool execution."""
        result = mock_tool.execute({"param1": "test"}, tool_context)
        assert result.success is True
        assert result.data == {"result": "success", "param1": "test"}
        assert mock_tool.metrics.total_executions == 1
        assert mock_tool.metrics.failed_executions == 0

    def test_execute_failure(self, mock_tool, tool_context):
        """Test failed tool execution."""
        result = mock_tool.execute({"param1": "test", "should_fail": True}, tool_context)
        assert result.success is False
        assert "Execution failed as requested" in result.error_message
        assert mock_tool.metrics.total_executions == 1
        assert mock_tool.metrics.failed_executions == 1

    def test_validate_params(self, mock_tool):
        """Test parameter validation."""
        assert mock_tool.validate_params({"param1": "test"}) is True
        assert mock_tool.validate_params({}) is False
        assert mock_tool.validate_params(None) is False

    def test_get_metadata(self, mock_tool):
        """Test metadata retrieval."""
        metadata = mock_tool.get_metadata()
        assert metadata["name"] == "mock_tool"
        assert metadata["description"] == "A mock tool for testing"
        assert metadata["version"] == "1.0.0"
        assert metadata["compatible_versions"] == ["0.9.0"]
        assert metadata["required_params"] == ["param1"]
        assert "metrics" in metadata

class TestToolRegistry:
    """Test suite for ToolRegistry."""

    def test_initialization(self, tool_registry):
        """Test ToolRegistry initialization."""
        assert len(tool_registry._tools) == 0
        assert len(tool_registry._version_history) == 0
        assert len(tool_registry._chain_definitions) == 0

    def test_register_tool(self, tool_registry):
        """Test tool registration."""
        tool_registry.register(MockTool)
        assert "mock_tool" in tool_registry._tools
        assert len(tool_registry._version_history["mock_tool"]) == 1
        assert tool_registry._version_history["mock_tool"][0] == "1.0.0"

    def test_register_tool_version_update(self, tool_registry):
        """Test tool registration with version update."""
        # Register original version
        tool_registry.register(MockTool)

        # Create new version
        class UpdatedMockTool(MockTool):
            version = "1.1.0"

        # Register new version
        tool_registry.register(UpdatedMockTool)

        assert tool_registry._tools["mock_tool"].version == "1.1.0"
        assert "1.0.0" in tool_registry._tools["mock_tool"].compatible_versions

    def test_define_chain(self, tool_registry):
        """Test chain definition."""
        chain = [("tool1", 0.5), ("tool2", 0.7)]
        tool_registry.define_chain("test_intent", chain)
        assert "test_intent" in tool_registry._chain_definitions
        assert tool_registry._chain_definitions["test_intent"] == chain

    def test_execute_chain(self, tool_registry):
        """Test chain execution."""
        # Register mock tool
        tool_registry.register(MockTool)

        # Define chain
        tool_registry.define_chain("test_intent", [("mock_tool", 0.5)])

        # Execute chain
        results = tool_registry.execute_chain(
            {
                "intent": "test_intent",
                "params": {"param1": "test"},
                "confidence": 0.9,
                "entities": {}
            }
        )

        assert len(results) == 1
        assert results[0].success is True

    def test_select_tool(self, tool_registry):
        """Test tool selection."""
        # Register mock tool
        tool_registry.register(MockTool)

        # Test selection with matching intent
        selected_tool = tool_registry.select_tool(
            {
                "intent": "test_intent",
                "confidence": 0.9,
                "entities": {}
            }
        )
        assert isinstance(selected_tool, MockTool)

        # Test selection with non-matching intent
        selected_tool = tool_registry.select_tool(
            {
                "intent": "unknown_intent",
                "confidence": 0.9,
                "entities": {}
            }
        )
        assert selected_tool is None

    def test_get_all_tools(self, tool_registry):
        """Test retrieving all registered tools."""
        tool_registry.register(MockTool)
        tools = tool_registry.get_all_tools()
        assert len(tools) == 1
        assert isinstance(tools[0], MockTool)

    def test_get_tool_metadata(self, tool_registry):
        """Test retrieving metadata for all tools."""
        tool_registry.register(MockTool)
        metadata = tool_registry.get_tool_metadata()
        assert "mock_tool" in metadata
        assert metadata["mock_tool"]["version"] == "1.0.0"
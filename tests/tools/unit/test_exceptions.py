"""Unit tests for tool exceptions."""
import pytest
from src.tools.exceptions import (
    ToolExecutionError,
    ToolNotFoundError,
    ToolValidationError
)

class TestToolExceptions:
    """Test suite for tool-related exceptions."""

    def test_tool_execution_error(self):
        """Test ToolExecutionError exception."""
        message = "Failed to execute tool"
        with pytest.raises(ToolExecutionError) as exc_info:
            raise ToolExecutionError(message)
        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, Exception)

    def test_tool_not_found_error(self):
        """Test ToolNotFoundError exception."""
        tool_name = "nonexistent_tool"
        message = f"Tool not found: {tool_name}"
        with pytest.raises(ToolNotFoundError) as exc_info:
            raise ToolNotFoundError(message)
        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, Exception)

    def test_tool_validation_error(self):
        """Test ToolValidationError exception."""
        message = "Invalid tool parameters"
        with pytest.raises(ToolValidationError) as exc_info:
            raise ToolValidationError(message)
        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, Exception)

    def test_exception_inheritance(self):
        """Test that all exceptions inherit from Exception."""
        assert issubclass(ToolExecutionError, Exception)
        assert issubclass(ToolNotFoundError, Exception)
        assert issubclass(ToolValidationError, Exception)

    def test_error_with_custom_data(self):
        """Test exceptions with additional error data."""
        error_data = {"param": "value", "code": 500}
        exc = ToolExecutionError("Error message", error_data)
        assert hasattr(exc, "args")
        assert len(exc.args) == 2
        assert exc.args[1] == error_data

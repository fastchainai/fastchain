"""Custom exceptions for tool-related errors."""

class ToolExecutionError(Exception):
    """Raised when a tool fails to execute."""
    pass

class ToolNotFoundError(Exception):
    """Raised when a requested tool is not found."""
    pass

class ToolValidationError(Exception):
    """Raised when tool parameters validation fails."""
    pass

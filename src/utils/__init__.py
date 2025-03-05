"""Utility functions and classes for the Intent Agent."""
def get_task_router():
    """Lazy import of TaskRouter to avoid circular dependencies."""
    from .task_router import TaskRouter
    return TaskRouter

from .formatters import format_confidence_color

__all__ = ['get_task_router', 'format_confidence_color']
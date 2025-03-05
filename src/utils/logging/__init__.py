"""
A standardizsd logging package for Helix agents that integrates Python's logging
with structured logging via structlog. Provides a common Logging interface for all Helix agents.
"""

from .logger import Logging

__all__ = ["Logging"]

__version__ = "0.1.0"

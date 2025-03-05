"""
File: src/utils/logging/logger.py
Description: Defines the Logging class that standardizes logging across the FastChain AI platform.
"""

import os
import logging
import structlog
from pathlib import Path
from typing import Optional, Dict, Any

from .config import (
    DEFAULT_LOG_FORMAT,
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_FILE_PATH,
    get_environment_settings,
)
from .file_handler import FileHandler
from .handler import get_handler
from src.config.config import settings

class Logging:
    def __init__(
        self,
        name: str,
        level: Optional[str] = None,
        format_str: Optional[str] = None,
        environment: Optional[str] = None,
        backend: Optional[str] = None,
        backend_config: Optional[Dict[str, Any]] = None,
        log_file: str = DEFAULT_LOG_FILE_PATH,
    ):
        """Initialize logging with the given configuration."""
        self.name = name
        self.context = {}

        # If environment is provided, use its defaults when level/format not explicitly set
        if environment:
            env_settings = get_environment_settings(environment)
            if level is None:
                level = env_settings["log_level"]
            if format_str is None:
                format_str = env_settings["log_format"]

        # Fallback to defaults if still not provided
        if level is None:
            level = DEFAULT_LOG_LEVEL
        if format_str is None:
            format_str = DEFAULT_LOG_FORMAT

        # Convert level string to numeric if needed
        numeric_level = (
            level if isinstance(level, int) else logging._nameToLevel.get(level.upper(), logging.INFO)
        )

        # Setup basic logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(numeric_level)
        # Clear existing handlers
        self.logger.handlers = []

        try:
            if backend:
                # Use the specified backend handler
                backend_handler = get_handler(backend, backend_config or {})
                self.logger.addHandler(backend_handler)
            else:
                # Check if file logging is enabled
                enable_file_logging = settings.get('ENABLE_FILE_LOGGING', False)

                if enable_file_logging:
                    # Create logs directory if it doesn't exist and file logging is enabled
                    log_dir = os.path.dirname(log_file)
                    try:
                        Path(log_dir).mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        print(f"Warning: Failed to create log directory {log_dir}: {e}")
                        # Fall back to current directory
                        log_file = "app.log"

                    # Add file handler only if enabled
                    file_handler = FileHandler(log_file)
                    formatter = logging.Formatter(format_str)
                    file_handler.setFormatter(formatter)
                    self.logger.addHandler(file_handler)

            # Always add console logging regardless of file logging setting
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(format_str)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

            # Configure structlog for structured logging
            structlog.configure(
                processors=[
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.add_logger_name,
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer(),
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )
            self.structured_logger = structlog.wrap_logger(
                self.logger,
                initial_values={
                    "logger_name": name,
                    "environment": environment or "development"
                }
            )

        except Exception as e:
            # If structured logging setup fails, fall back to basic logging
            print(f"Warning: Failed to setup structured logging: {e}")
            self.structured_logger = self.logger

    def bind_context(self, **kwargs) -> None:
        """Bind additional context to all subsequent log messages."""
        self.context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all bound context data."""
        self.context.clear()

    def _log(self, level: str, msg: str, **kwargs) -> None:
        """Internal logging method with context handling."""
        try:
            log_context = {**self.context, **kwargs}
            logger_method = getattr(self.structured_logger, level)
            logger_method(msg, **log_context)
        except Exception as e:
            print(f"Warning: Failed to log {level} message: {e}")
            fallback_logger = getattr(self.logger, level)
            fallback_logger(msg)

    def debug(self, msg: str, **kwargs) -> None:
        """Log debug message with context."""
        self._log("debug", msg, **kwargs)

    def info(self, msg: str, **kwargs) -> None:
        """Log info message with context."""
        self._log("info", msg, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        """Log warning message with context."""
        self._log("warning", msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        """Log error message with context."""
        self._log("error", msg, **kwargs)

    def critical(self, msg: str, **kwargs) -> None:
        """Log critical message with context."""
        self._log("critical", msg, **kwargs)
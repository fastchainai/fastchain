"""
File: src/utils/logging/formatter.py
Description: Provides custom formatters for logging, including a JSON formatter for structured logging.
Date: 24/02/2025
Version: 1.0.0
Repository: https://github.com/
"""

import json
import logging

class JSONFormatter(logging.Formatter):
    """
    Formatter to output log records in JSON format.
    """

    def __init__(self, fmt=None, datefmt=None, style='%', extra_fields=None):
        """
        Initialize the JSONFormatter.

        Args:
            fmt (str): Log message format.
            datefmt (str): Date format string.
            style (str): Formatting style.
            extra_fields (dict): Additional fields to include.
        """
        super().__init__(fmt, datefmt, style)
        self.extra_fields = extra_fields or {}

    def format(self, record):
        """
        Format the log record as JSON.
        """
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Merge any extra fields provided in the record or via init.
        if hasattr(record, "extra"):
            log_record.update(record.extra)
        log_record.update(self.extra_fields)
        return json.dumps(log_record)


def get_default_formatter(structured=False, format_str=(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")):
    """
    Returns the default formatter. If structured is True, returns a JSON
    formatter; otherwise, returns a standard logging formatter.

    Args:
        structured (bool): Flag to determine formatter type.
        format_str (str): Log format string.

    Returns:
        logging.Formatter: Formatter instance.
    """
    if structured:
        return JSONFormatter(fmt=format_str)
    return logging.Formatter(format_str)

"""
File: src/utils/logging/handler.py
Description: Provides the get_handler function to return an external backend handler based on the specified backend. This module is used only when a backend is provided.
Date: 24/02/2025
Version: 1.0.0
Repository: https://github.com/
"""

from typing import Dict, Any
from .handlers.elasticsearch_handler import ElasticsearchHandler
from .handlers.kafka_handler import KafkaHandler
from .handlers.loki_handler import LokiHandler

def get_handler(backend: str, config: Dict[str, Any]):
    """
    Returns a logging handler based on the specified backend.

    Args:
        backend (str): The name of the backend to use ('loki', 'elasticsearch', 'kafka')
        config (dict): Configuration for the handler

    Returns:
        logging.Handler: The configured handler for the specified backend

    Raises:
        ValueError: If an unsupported backend is specified
    """
    handlers = {
        "loki": LokiHandler,
        "elasticsearch": ElasticsearchHandler,
        "kafka": KafkaHandler
    }

    handler_class = handlers.get(backend.lower())
    if handler_class is None:
        raise ValueError(f"Unsupported logging backend: {backend}")

    return handler_class(config)
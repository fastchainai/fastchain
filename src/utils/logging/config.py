"""
File: srcutils/logging/config.py
Description: Default configuration values for , including
 environment-specific settings.
Date: 24/02/2025
Version: 1.1.0
Repository: http://
"""
from src.config.config import settings

DEFAULT_LOG_LEVEL = settings.get("DEFAULT_LOG_LEVEL", "INFO")
DEFAULT_LOG_FORMAT = settings.get("DEFAULT_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
DEFAULT_LOG_DATE_FORMAT = settings.get("DEFAULT_LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")
DEFAULT_LOG_FILE_PATH = settings.get("DEFAULT_LOG_FILE_PATH", "logs/app.log")

ENVIRONMENT_SETTINGS = {
    "development": {
        "log_level": "DEBUG",
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
    "testing": {
        "log_level": "DEBUG",
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
    "staging": {
        "log_level": "INFO",
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
    "production": {
        "log_level": "WARNING",
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
}

def get_environment_settings(environment: str):
    """
    Returns log settings based on the provided environment.
    
    Args:
        environment (str): The environment name (e.g., development, testing,
            staging, production).
    
    Returns:
        dict: A dictionary with 'log_level' and 'log_format' keys.
    """
    return ENVIRONMENT_SETTINGS.get(
        environment.lower(),
        {"log_level": DEFAULT_LOG_LEVEL, "log_format": DEFAULT_LOG_FORMAT},
    )

"""
Configuration Module

This module sets up and manages application configuration using Dynaconf.
It provides a robust, type-safe configuration management system with support for:
- Multiple environments (development, staging, production)
- Secret management
- Dynamic configuration reloading
- Validation and type checking
- Comprehensive logging
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union
from dynaconf import Dynaconf, ValidationError, Validator
import structlog

# Initialize structured logging
logger = structlog.get_logger(__name__)

class ConfigurationError(Exception):
    """Raised when there is an error in configuration loading or validation."""
    pass

def create_validators() -> List[Validator]:
    """Create validation rules for configuration settings."""
    return [
        # Server configuration
        Validator("FASTAPI_PORT", must_exist=True, is_type_of=int),
        Validator("FASTAPI_HOST", must_exist=True, is_type_of=str),

        # Redis configuration
        Validator("USE_REDIS_CACHING", is_type_of=bool),
        Validator("REDIS_URL", must_exist=True, when=Validator("USE_REDIS_CACHING", eq=True)),

        # Feature flags
        Validator("TIME_BASED_EXPIRATION", is_type_of=bool),
        Validator("SESSION_EXPIRATION_SECONDS", is_type_of=int),

        # Logging configuration
        Validator("DEFAULT_LOG_LEVEL", default="INFO"),
        Validator("DEFAULT_LOG_FORMAT", must_exist=True),
    ]

# Initialize Dynaconf with our settings
settings = Dynaconf(
    envvar_prefix="FASTCHAIN",
    settings_files=[
        "src/config/settings.toml",  # Base settings
        "src/config/settings.local.toml",  # Local overrides (git-ignored)
        "src/config/.secrets.toml",  # Sensitive settings (git-ignored)
    ],
    environments=True,
    load_dotenv=True,
    merge_enabled=True,
    validators=create_validators(),
)

def validate_config() -> None:
    """
    Validate the configuration settings.
    Raises ConfigurationError if validation fails.
    """
    try:
        settings.validators.validate()
    except ValidationError as e:
        error_msg = f"Configuration validation failed: {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e

def get_setting(key: str, default: Any = None, cast: type = None) -> Any:
    """
    Safely retrieve a configuration setting with optional type casting.

    Args:
        key: The configuration key to retrieve
        default: Default value if key doesn't exist
        cast: Optional type to cast the value to

    Returns:
        The configuration value
    """
    try:
        value = settings.get(key, default=default)
        if cast and value is not None:
            value = cast(value)
        return value
    except Exception as e:
        logger.warning(f"Error retrieving configuration key '{key}': {str(e)}")
        return default

def reload_config() -> None:
    """
    Reload the configuration settings at runtime.
    Validates the configuration after reloading.

    Raises:
        ConfigurationError: If reloading or validation fails
    """
    try:
        settings.reload()
        validate_config()
        logger.info("Configuration reloaded and validated successfully")
    except Exception as e:
        error_msg = f"Error reloading configuration: {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e

def get_environment() -> str:
    """Get the current environment name."""
    return settings.current_env.lower()

def is_development() -> bool:
    """Check if running in development environment."""
    return get_environment() == "development"

def is_production() -> bool:
    """Check if running in production environment."""
    return get_environment() == "production"

# Validate configuration on module load
try:
    validate_config()
    logger.info(
        "Configuration loaded successfully",
        environment=get_environment(),
        features_enabled={
            "redis": settings.get("USE_REDIS_CACHING", False),
            "async": settings.get("ASYNC_OPERATIONS", False),
            "telemetry": settings.get("ENABLE_TELEMETRY", False)
        }
    )
except ConfigurationError as e:
    logger.error(f"Failed to load configuration: {str(e)}")
    raise

# Export the settings instance as the primary interface
__all__ = ["settings", "reload_config", "get_setting", "is_development", "is_production"]
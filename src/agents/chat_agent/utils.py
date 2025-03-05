"""Utility functions for the Chat Agent with enhanced security and compliance."""
import json
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import html
import uuid

logger = logging.getLogger(__name__)

def format_chat_response(
    response: str,
    metadata: Optional[Dict[str, Any]] = None,
    security_level: str = "standard"
) -> Dict[str, Any]:
    """
    Format a chat response with enhanced security measures.

    Args:
        response: The response text
        metadata: Optional metadata to include
        security_level: Security level for response formatting

    Returns:
        Dict containing the formatted and secured response
    """
    # Sanitize the response
    sanitized_response = sanitize_message(response)

    formatted_response = {
        "text": sanitized_response,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "chat_response",
        "security_checksum": generate_checksum(sanitized_response)
    }

    if metadata:
        # Sanitize metadata before including
        sanitized_metadata = sanitize_metadata(metadata)
        formatted_response["metadata"] = sanitized_metadata

    return formatted_response

def validate_chat_request(request: Dict[str, Any]) -> bool:
    """
    Validate a chat request with enhanced security checks.

    Args:
        request: The request to validate

    Returns:
        bool: True if valid and secure, False otherwise
    """
    try:
        # Required fields check
        required_fields = ["message", "timestamp"]
        if not all(field in request for field in required_fields):
            return False

        # Message content validation
        if not is_safe_content(request["message"]):
            logger.warning("Potentially unsafe content detected in message")
            return False

        # Timestamp validation (prevent replay attacks)
        if not is_valid_timestamp(request["timestamp"]):
            logger.warning("Invalid timestamp in request")
            return False

        return True

    except Exception as e:
        logger.error(f"Error validating chat request: {e}")
        return False

def sanitize_message(message: str) -> str:
    """
    Sanitize a chat message with comprehensive security measures.

    Args:
        message: The message to sanitize

    Returns:
        str: The sanitized message
    """
    if not message:
        return ""

    # HTML escape
    sanitized = html.escape(message)

    # Remove potentially dangerous patterns
    sanitized = remove_dangerous_patterns(sanitized)

    # Normalize whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    # Length validation
    max_length = 4096  # Configurable
    if len(sanitized) > max_length:
        logger.warning(f"Message truncated from {len(message)} to {max_length} characters")
        sanitized = sanitized[:max_length]

    return sanitized

def remove_dangerous_patterns(text: str) -> str:
    """Remove potentially dangerous patterns from text."""
    # Remove potential script tags
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove potential SQL injection patterns
    text = re.sub(r'(\b(select|insert|update|delete|drop|union|exec)\b)', '', text, flags=re.IGNORECASE)

    # Remove potential command injection patterns
    text = re.sub(r'[;&|`]', '', text)

    return text

def is_safe_content(content: str) -> bool:
    """
    Check if content is safe for processing.

    Args:
        content: The content to check

    Returns:
        bool: True if content is safe, False otherwise
    """
    # Check for maximum length
    if len(content) > 4096:
        return False

    # Check for dangerous patterns
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'data:text/html',
        r'vbscript:',
        r'onload=',
        r'onerror='
    ]

    return not any(re.search(pattern, content, re.IGNORECASE) for pattern in dangerous_patterns)

def is_valid_timestamp(timestamp: str) -> bool:
    """
    Validate timestamp to prevent replay attacks.

    Args:
        timestamp: The timestamp to validate

    Returns:
        bool: True if timestamp is valid, False otherwise
    """
    try:
        timestamp_dt = datetime.fromisoformat(timestamp)
        now = datetime.utcnow()
        # Allow 5 minutes of clock skew
        return abs((now - timestamp_dt).total_seconds()) <= 300
    except Exception:
        return False

def generate_checksum(content: str) -> str:
    """
    Generate a security checksum for content verification.

    Args:
        content: The content to checksum

    Returns:
        str: The generated checksum
    """
    return hashlib.sha256(content.encode()).hexdigest()

def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize metadata fields for security.

    Args:
        metadata: The metadata to sanitize

    Returns:
        Dict: Sanitized metadata
    """
    sanitized = {}
    for key, value in metadata.items():
        # Sanitize keys
        safe_key = sanitize_message(str(key))

        # Sanitize values based on type
        if isinstance(value, str):
            safe_value = sanitize_message(value)
        elif isinstance(value, (int, float, bool)):
            safe_value = value  # Primitive types are safe
        elif isinstance(value, dict):
            safe_value = sanitize_metadata(value)  # Recursive sanitization
        elif isinstance(value, list):
            safe_value = [sanitize_message(str(v)) if isinstance(v, str) else v for v in value]
        else:
            # Skip unsupported types
            logger.warning(f"Skipping unsupported metadata type: {type(value)}")
            continue

        sanitized[safe_key] = safe_value

    return sanitized

def load_agent_config(config_path: str) -> Dict[str, Any]:
    """
    Load agent configuration with security validation.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dict containing the validated configuration
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Validate configuration
        if not validate_config(config):
            raise ValueError("Invalid configuration detected")

        return config
    except Exception as e:
        logger.error(f"Error loading agent configuration: {e}")
        raise

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration for security and completeness.

    Args:
        config: The configuration to validate

    Returns:
        bool: True if configuration is valid, False otherwise
    """
    required_fields = [
        "agent_name",
        "version",
        "capabilities",
        "status",
        "configuration"
    ]

    # Check required fields
    if not all(field in config for field in required_fields):
        return False

    # Validate security settings
    security_config = config.get("configuration", {}).get("security", {})
    if not security_config:
        return False

    return True

def format_error_response(error: Exception) -> Dict[str, Any]:
    """
    Format an error response with security considerations.

    Args:
        error: The exception to format

    Returns:
        Dict containing the secured error response
    """
    # Generic error message for security
    safe_error_message = "An error occurred processing your request"

    if isinstance(error, ValueError):
        # Safe to expose validation errors
        safe_error_message = str(error)

    return {
        "error": safe_error_message,
        "type": "error",
        "timestamp": datetime.utcnow().isoformat(),
        "reference_id": generate_error_reference()
    }

def generate_error_reference() -> str:
    """Generate a unique error reference ID."""
    return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:12]
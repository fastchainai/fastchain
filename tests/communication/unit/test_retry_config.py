"""Unit tests for RetryConfig in communication module."""
import pytest
from src.communication.communication import RetryConfig
from src.config.config import settings

def test_retry_config_defaults():
    """Test RetryConfig with default values."""
    config = RetryConfig()

    assert config.max_retries == settings.get("TASK_MAX_RETRIES", 3)
    assert config.base_delay == settings.get("TASK_RETRY_DELAY", 1.0)
    assert config.max_delay == settings.get("TASK_MAX_RETRY_DELAY", 10.0)
    assert config.timeout == settings.get("TASK_DEFAULT_TIMEOUT", 30.0)

def test_retry_config_custom_values():
    """Test RetryConfig with custom values."""
    config = RetryConfig(
        max_retries=5,
        base_delay=2.0,
        max_delay=15.0,
        timeout=45.0
    )

    assert config.max_retries == 5
    assert config.base_delay == 2.0
    assert config.max_delay == 15.0
    assert config.timeout == 45.0

def test_retry_config_validation():
    """Test validation of RetryConfig values."""
    # Test negative max_retries
    with pytest.raises(ValueError):
        RetryConfig(max_retries=-1)

    # Test negative delays
    with pytest.raises(ValueError):
        RetryConfig(base_delay=-1.0)

    with pytest.raises(ValueError):
        RetryConfig(max_delay=-1.0)

    # Test negative timeout
    with pytest.raises(ValueError):
        RetryConfig(timeout=-1.0)

    # Test max_delay less than base_delay
    with pytest.raises(ValueError):
        RetryConfig(base_delay=5.0, max_delay=3.0)

def test_retry_config_zero_values():
    """Test RetryConfig with zero values."""
    # Zero retries should be valid
    config = RetryConfig(max_retries=0)
    assert config.max_retries == 0

    # Zero delay should be valid
    config = RetryConfig(base_delay=0.0)
    assert config.base_delay == 0.0

    config = RetryConfig(max_delay=0.0)
    assert config.max_delay == 0.0

    # Zero timeout means no timeout
    config = RetryConfig(timeout=0.0)
    assert config.timeout == 0.0

def test_retry_config_edge_cases():
    """Test RetryConfig edge cases and boundary conditions."""
    # Test maximum allowed values
    config = RetryConfig(
        max_retries=100,  # Large but reasonable
        base_delay=60.0,  # 1 minute
        max_delay=300.0,  # 5 minutes
        timeout=3600.0    # 1 hour
    )
    assert config.max_retries == 100
    assert config.base_delay == 60.0
    assert config.max_delay == 300.0
    assert config.timeout == 3600.0

    # Test equal base_delay and max_delay
    config = RetryConfig(base_delay=5.0, max_delay=5.0)
    assert config.base_delay == config.max_delay

def test_retry_config_type_validation():
    """Test type validation of RetryConfig values."""
    with pytest.raises(ValueError):
        RetryConfig(max_retries=1.5)  # Must be integer

    with pytest.raises(ValueError):
        RetryConfig(base_delay="1.0")  # Must be float

    with pytest.raises(ValueError):
        RetryConfig(max_delay="2.0")  # Must be float

    with pytest.raises(ValueError):
        RetryConfig(timeout="30.0")  # Must be float
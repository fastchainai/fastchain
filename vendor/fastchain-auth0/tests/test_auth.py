"""Tests for Auth0 authentication functionality."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from jose.exceptions import JWTError
import time
import asyncio
import aiohttp
from fastchain_auth0 import TokenPayload
from fastchain_auth0.rate_limiting import AsyncTokenRateLimiter

class AsyncContextManagerMock:
    """Helper class to mock async context managers."""
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None

def test_auth0_config(auth0_config):
    """Test Auth0Config initialization and methods."""
    assert auth0_config.get_jwks_url() == "https://test.auth0.com/.well-known/jwks.json"
    assert auth0_config.get_issuer() == "https://test.auth0.com/"

@pytest.mark.asyncio
async def test_get_jwks(auth0_manager):
    """Test JWKS fetching."""
    # Clear the JWKS cache
    auth0_manager._jwks_cache = None
    auth0_manager._jwks_timestamp = 0

    # Create mock response with async json method
    mock_response = AsyncMock()
    mock_response.json.return_value = {"keys": []}
    mock_response.status = 200
    mock_response.raise_for_status = Mock()

    # Create a regular function that returns our async context manager
    def mock_get(*args, **kwargs):
        return AsyncContextManagerMock(mock_response)

    # Set up the session mock
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = mock_get

    with patch.object(auth0_manager, '_session', mock_session):
        # Test initial fetch
        jwks = await auth0_manager.get_jwks()
        assert jwks == {"keys": []}
        mock_response.raise_for_status.assert_called_once()

        # Test cache hit
        mock_response.raise_for_status.reset_mock()
        jwks = await auth0_manager.get_jwks()
        assert jwks == {"keys": []}
        mock_response.raise_for_status.assert_not_called()  # Should use cache

@pytest.mark.asyncio
async def test_verify_token(auth0_manager):
    """Test token verification."""
    mock_header = {"kid": "test-kid"}
    mock_payload = {
        "sub": "test-sub",
        "iss": "https://test.auth0.com/",
        "aud": ["test-api"],
        "exp": 1600000000,
        "iat": 1500000000
    }

    with patch('jose.jwt.get_unverified_header', return_value=mock_header), \
         patch('jose.jwt.decode', return_value=mock_payload):

        # Pre-populate JWKS cache for this test
        auth0_manager._jwks_cache = {
            "keys": [{
                "kid": "test-kid",
                "kty": "RSA",
                "use": "sig",
                "n": "test",
                "e": "test"
            }]
        }
        auth0_manager._jwks_timestamp = time.time()

        payload = await auth0_manager.verify_token("test-token")
        assert isinstance(payload, TokenPayload)
        assert payload.sub == "test-sub"

@pytest.mark.asyncio
async def test_verify_token_invalid(auth0_manager):
    """Test token verification with invalid token."""
    mock_header = {"kid": "invalid-kid"}

    with patch('jose.jwt.get_unverified_header', return_value=mock_header):
        # Pre-populate JWKS cache for this test
        auth0_manager._jwks_cache = {
            "keys": [{
                "kid": "test-kid",
                "kty": "RSA",
                "use": "sig",
                "n": "test",
                "e": "test"
            }]
        }
        auth0_manager._jwks_timestamp = time.time()

        with pytest.raises(JWTError) as exc_info:
            await auth0_manager.verify_token("invalid-token")
        assert "No matching key found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting functionality."""
    # Configure a strict rate limit for testing
    rate_limiter = AsyncTokenRateLimiter(max_requests=2, window_seconds=1)

    mock_token = "test-token"

    # First two requests should work
    assert await rate_limiter.is_allowed(mock_token)
    assert await rate_limiter.is_allowed(mock_token)

    # Third request should be blocked
    assert not await rate_limiter.is_allowed(mock_token)

    # Get remaining requests info
    remaining, reset_in = await rate_limiter.get_remaining(mock_token)
    assert remaining == 0
    assert reset_in > 0

@pytest.mark.asyncio
async def test_cleanup_task():
    """Test the cleanup task functionality."""
    rate_limiter = AsyncTokenRateLimiter(max_requests=2, window_seconds=1)
    mock_token = "test-token"

    # Add some requests
    await rate_limiter.is_allowed(mock_token)

    # Wait for more than the window
    await asyncio.sleep(1.1)

    # Manually trigger cleanup
    await rate_limiter.cleanup()

    # Verify the data was cleaned up
    remaining, reset_in = await rate_limiter.get_remaining(mock_token)
    assert remaining == 2  # Should be reset to max
    assert reset_in == 0  # No active window
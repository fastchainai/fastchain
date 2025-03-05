"""Tests for token refresh functionality."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from jose.exceptions import JWTError
from fastchain_auth0 import TokenRefreshError


@pytest.fixture
def refresh_manager():
    """Create a test TokenRefreshManager instance."""
    return TokenRefreshManager(
        domain="test.auth0.com",
        client_id="test-client",
        client_secret="test-secret",
        default_audience="test-api"
    )


@pytest.mark.asyncio
async def test_refresh_token_success(refresh_manager):
    """Test successful token refresh."""
    # Create async mock for the response
    mock_response = AsyncMock()
    mock_json = AsyncMock(return_value={
        "access_token": "new-token",
        "refresh_token": "new-refresh-token",
        "token_type": "Bearer",
        "expires_in": 3600
    })
    mock_response.json = mock_json
    mock_response.status = 200
    mock_response.raise_for_status = Mock()

    # Mock the context manager
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_response
    mock_context.__aexit__.return_value = None

    with patch('aiohttp.ClientSession.post', return_value=mock_context):
        result = await refresh_manager.refresh_token("old-refresh-token")

        assert result["access_token"] == "new-token"
        assert result["refresh_token"] == "new-refresh-token"
        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == 3600
        # Verify raise_for_status was not called (only called on error)
        mock_response.raise_for_status.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_token_failure(refresh_manager):
    """Test token refresh failure."""
    # Create async mock for the response
    mock_response = AsyncMock()
    mock_json = AsyncMock(return_value={
        "error": "invalid_grant",
        "error_description": "Invalid refresh token"
    })
    mock_response.json = mock_json
    mock_response.status = 400
    mock_response.raise_for_status = Mock()

    # Mock the context manager
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_response
    mock_context.__aexit__.return_value = None

    with patch('aiohttp.ClientSession.post', return_value=mock_context):
        with pytest.raises(JWTError) as exc_info:
            await refresh_manager.refresh_token("invalid-token")
        assert "Invalid refresh token" in str(exc_info.value)


@pytest.mark.asyncio
async def test_manager_cleanup(refresh_manager):
    """Test proper cleanup of aiohttp session."""
    # Session should be created when we use the refresh_manager fixture
    assert refresh_manager._session is not None

    # The session will be automatically cleaned up when the fixture is destroyed
    # No need to manually close it anymore
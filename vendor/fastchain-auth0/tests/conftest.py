import os
import sys
import pytest
import pytest_asyncio
from fastchain_auth0 import Auth0Config, Auth0Manager, TokenRefreshManager

# Add the package parent directory to sys.path
package_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if package_path not in sys.path:
    sys.path.insert(0, package_path)

@pytest.fixture
def auth0_config():
    """Create a test Auth0 configuration."""
    return Auth0Config(
        domain="test.auth0.com",
        api_audience="test-api",
        algorithms=["RS256"]
    )

@pytest_asyncio.fixture
async def auth0_manager(auth0_config):
    """Create a test Auth0Manager instance with automatic cleanup."""
    manager = Auth0Manager(auth0_config)
    await manager.__aenter__()
    try:
        yield manager
    finally:
        await manager.__aexit__(None, None, None)

@pytest_asyncio.fixture
async def refresh_manager():
    """Create a test TokenRefreshManager instance with automatic cleanup."""
    manager = TokenRefreshManager(
        domain="test.auth0.com",
        client_id="test-client",
        client_secret="test-secret",
        default_audience="test-api"
    )
    await manager.__aenter__()
    try:
        yield manager
    finally:
        await manager.__aexit__(None, None, None)
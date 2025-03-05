"""Unit tests for system health endpoint."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from src.api.v1.system.endpoints.health import router, check_redis_connection
from src.config.config import settings

@pytest.fixture
def test_client():
    """Create a test client."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix="/system/health")
    return TestClient(app)

@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return Mock(spec=dict)

class TestHealthEndpoint:
    """Test suite for health check endpoint."""

    async def test_health_check_redis_disabled(self, test_client, mock_settings):
        """Test health check when Redis is disabled."""
        with patch('src.api.v1.system.endpoints.health.settings', mock_settings):
            mock_settings.get.return_value = False
            response = test_client.get("/system/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert data["checks"]["redis"]["status"] == "disabled"

    async def test_health_check_redis_enabled_healthy(self, test_client, mock_settings):
        """Test health check when Redis is enabled and healthy."""
        with patch('src.api.v1.system.endpoints.health.settings', mock_settings), \
             patch('redis.Redis') as mock_redis:

            mock_settings.get.side_effect = lambda key, default=None: {
                "USE_REDIS_CACHING": True,
                "REDIS_URL": "redis://localhost:6379/0"
            }.get(key, default)

            mock_redis_instance = Mock()
            mock_redis.from_url.return_value = mock_redis_instance

            response = test_client.get("/system/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["checks"]["redis"]["status"] == "healthy"

    async def test_health_check_redis_enabled_unhealthy(self, test_client, mock_settings):
        """Test health check when Redis is enabled but unhealthy."""
        with patch('src.api.v1.system.endpoints.health.settings', mock_settings), \
             patch('redis.Redis') as mock_redis:

            mock_settings.get.side_effect = lambda key, default=None: {
                "USE_REDIS_CACHING": True,
                "REDIS_URL": "redis://localhost:6379/0"
            }.get(key, default)

            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = Exception("Connection failed")
            mock_redis.from_url.return_value = mock_redis_instance

            response = test_client.get("/system/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["checks"]["redis"]["status"] == "unhealthy"
            assert "error" in data["checks"]["redis"]

    @pytest.mark.asyncio
    async def test_check_redis_connection_disabled(self, mock_settings):
        """Test Redis connection check when disabled."""
        with patch('src.api.v1.system.endpoints.health.settings', mock_settings):
            mock_settings.get.return_value = False
            result = await check_redis_connection()
            assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_check_redis_connection_enabled_success(self, mock_settings):
        """Test Redis connection check when enabled and successful."""
        with patch('src.api.v1.system.endpoints.health.settings', mock_settings), \
             patch('redis.Redis') as mock_redis:

            mock_settings.get.side_effect = lambda key, default=None: {
                "USE_REDIS_CACHING": True,
                "REDIS_URL": "redis://localhost:6379/0"
            }.get(key, default)

            mock_redis_instance = Mock()
            mock_redis.from_url.return_value = mock_redis_instance

            result = await check_redis_connection()
            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_redis_connection_enabled_failure(self, mock_settings):
        """Test Redis connection check when enabled but fails."""
        with patch('src.api.v1.system.endpoints.health.settings', mock_settings), \
             patch('redis.Redis') as mock_redis:

            mock_settings.get.side_effect = lambda key, default=None: {
                "USE_REDIS_CACHING": True,
                "REDIS_URL": "redis://localhost:6379/0"
            }.get(key, default)

            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = Exception("Connection failed")
            mock_redis.from_url.return_value = mock_redis_instance

            result = await check_redis_connection()
            assert result["status"] == "unhealthy"
            assert "error" in result
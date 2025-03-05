"""Unit tests for API v1 routers."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, ANY
from datetime import datetime
import structlog
from src.api.v1.routers import router

@pytest.fixture
def test_client():
    """Create a test client."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)

@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return structlog.get_logger()

class TestAPIRouter:
    """Test suite for API router configuration."""

    def test_health_check_endpoint(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0"
        assert "timestamp" in data

    def test_health_check_with_trailing_slash(self, test_client):
        """Test health check endpoint with trailing slash."""
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_registered_routes(self, test_client):
        """Test that all expected routes are registered."""
        app = test_client.app
        routes = [route for route in app.router.routes]
        paths = {route.path for route in routes}

        # Check core prefixes are registered
        assert "/api/v1/agents/registry" in paths
        assert "/api/v1/chat" in paths
        assert "/api/v1/intent/process" in paths
        assert "/api/v1/admin/config" in paths
        assert "/api/v1/system/status" in paths

    def test_route_tags(self, test_client):
        """Test that routes have correct tags."""
        app = test_client.app
        tags = set()
        for route in app.router.routes:
            if hasattr(route, "tags"):
                tags.update(route.tags)

        expected_tags = {
            "Agent Registry",
            "Chat Agent",
            "Intent Processing",
            "Administration",
            "System"
        }
        assert expected_tags.issubset(tags)

    def test_health_check_timestamp_format(self, test_client):
        """Test that health check timestamp is in ISO format."""
        response = test_client.get("/api/v1/health")
        data = response.json()
        timestamp = data["timestamp"]

        # Verify ISO format
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail("Timestamp is not in ISO format")

    @patch('src.api.v1.routers.structlog.get_logger')
    def test_route_logging(self, mock_get_logger, test_client):
        """Test that route access is properly logged."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        test_client.get("/api/v1/health")

        mock_logger.info.assert_called_with(
            "v1 API routes registered",
            routes=ANY
        )

    def test_router_prefix_consistency(self, test_client):
        """Test that router prefixes are consistent and well-formed."""
        app = test_client.app
        for route in app.router.routes:
            if hasattr(route, "path"):
                # Ensure path starts with /api/v1
                assert route.path.startswith("/api/v1")
                # Ensure no double slashes
                assert "//" not in route.path

    def test_admin_routes(self, test_client):
        """Test admin route configuration."""
        response = test_client.get("/api/v1/admin/config")
        assert response.status_code in [200, 401, 403]  # Depending on auth config

    def test_system_routes(self, test_client):
        """Test system route configuration."""
        response = test_client.get("/api/v1/system/status")
        assert response.status_code == 200

    def test_chat_routes(self, test_client):
        """Test chat route configuration."""
        response = test_client.get("/api/v1/chat")
        assert response.status_code in [200, 404]  # Depending on chat agent availability

    def test_intent_routes(self, test_client):
        """Test intent route configuration."""
        # Intent processing requires POST with data
        response = test_client.post("/api/v1/intent/process", json={"text": "test"})
        assert response.status_code in [200, 422]  # 422 if validation fails
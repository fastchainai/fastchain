"""Unit tests for system status endpoint."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import psutil
from datetime import datetime, timezone
from src.api.v1.system.endpoints.status import router, START_TIME

@pytest.fixture
def test_client():
    """Create a test client."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix="/system/status")
    return TestClient(app)

class TestStatusEndpoint:
    """Test suite for status endpoint."""

    def test_get_system_status_success(self, test_client):
        """Test successful system status retrieval."""
        # Mock psutil functions
        mock_cpu = 45.2
        mock_memory = Mock(
            total=17179869184,  # 16GB
            available=8589934592,  # 8GB
            percent=50.0
        )
        mock_disk = Mock(
            total=256060514304,  # 256GB
            free=128030257152,  # 128GB
            percent=50.0
        )

        with patch('psutil.cpu_percent', return_value=mock_cpu), \
             patch('psutil.virtual_memory', return_value=mock_memory), \
             patch('psutil.disk_usage', return_value=mock_disk), \
             patch('time.time', return_value=START_TIME + 3600):  # 1 hour uptime

            response = test_client.get("/system/status")
            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert data["status"] == "operational"
            assert "timestamp" in data
            assert data["uptime_seconds"] == pytest.approx(3600, rel=1e-2)

            # Verify resource metrics
            resources = data["resources"]
            assert resources["cpu"]["usage_percent"] == mock_cpu
            assert resources["memory"]["total"] == mock_memory.total
            assert resources["memory"]["available"] == mock_memory.available
            assert resources["memory"]["used_percent"] == mock_memory.percent
            assert resources["disk"]["total"] == mock_disk.total
            assert resources["disk"]["free"] == mock_disk.free
            assert resources["disk"]["used_percent"] == mock_disk.percent

    def test_get_system_status_psutil_error(self, test_client):
        """Test system status when psutil fails."""
        with patch('psutil.cpu_percent', side_effect=Exception("CPU info failed")):
            response = test_client.get("/system/status")
            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "error"
            assert "message" in data
            assert "timestamp" in data

    def test_status_timestamp_format(self, test_client):
        """Test that timestamp is in correct ISO format."""
        response = test_client.get("/system/status")
        data = response.json()
        timestamp = data["timestamp"]

        # Verify ISO format
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Timestamp is not in ISO format")

    def test_status_endpoint_logging(self, test_client):
        """Test that endpoint properly logs events."""
        with patch('logging.getLogger') as mock_logging:
            mock_logger = Mock()
            mock_logging.return_value = mock_logger

            test_client.get("/system/status")

            # Verify logging was called
            mock_logger.error.assert_not_called()  # Should not log errors on success

    def test_uptime_calculation(self, test_client):
        """Test uptime calculation is accurate."""
        test_time = START_TIME + 7200  # 2 hours uptime

        with patch('time.time', return_value=test_time):
            response = test_client.get("/system/status")
            data = response.json()

            assert data["uptime_seconds"] == pytest.approx(7200, rel=1e-2)

    def test_empty_routes(self, test_client):
        """Test both empty and slash routes return same response."""
        response1 = test_client.get("/system/status")
        response2 = test_client.get("/system/status/")

        assert response1.status_code == response2.status_code == 200
        assert response1.json()["status"] == response2.json()["status"] == "operational"
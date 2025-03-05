"""Unit tests for admin configuration endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.v1.admin.endpoints.config import router

@pytest.fixture
def test_client():
    """Create a test client."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix="/admin/config")  # Add the prefix to match production setup
    return TestClient(app)

@pytest.fixture
def mock_settings():
    """Create mock settings."""
    return {
        'test_setting': 'test_value',
        'debug_mode': True,
        'api_version': '1.0',
    }

class TestConfigEndpoints:
    """Test suite for configuration endpoints."""

    def test_get_config_settings_success(self, test_client, mock_settings):
        """Test successful retrieval of configuration settings."""
        with patch('src.api.v1.admin.endpoints.config.settings') as mock_config:
            mock_config.to_dict.return_value = mock_settings

            response = test_client.get("/admin/config/")

            assert response.status_code == 200
            assert response.json() == {"settings": mock_settings}

    def test_get_config_settings_error(self, test_client):
        """Test error handling in configuration retrieval."""
        with patch('src.api.v1.admin.endpoints.config.settings') as mock_config:
            mock_config.to_dict.side_effect = Exception("Test error")

            response = test_client.get("/admin/config/")

            assert response.status_code == 500
            assert "Failed to retrieve configuration settings" in response.json()["detail"]

    def test_update_config_setting_success(self, test_client):
        """Test successful update of a configuration setting."""
        test_setting = "test_setting"
        new_value = "new_value"
        request_data = {"value": new_value}  # Match ConfigUpdateRequest model

        with patch('src.api.v1.admin.endpoints.config.settings') as mock_config, \
             patch('src.api.v1.admin.endpoints.config.reload_config') as mock_reload:
            mock_config.exists.return_value = True
            mock_config.get.return_value = new_value

            response = test_client.post(f"/admin/config/{test_setting}", json=request_data)

            assert response.status_code == 200
            assert response.json() == {
                "status": "success",
                "message": f"Setting {test_setting} updated successfully"
            }
            mock_config.set.assert_called_once_with(test_setting, new_value)
            mock_reload.assert_called_once()

    def test_update_sensitive_setting_blocked(self, test_client):
        """Test blocking updates to sensitive settings."""
        sensitive_settings = ["secret_key", "api_key", "password", "token"]
        request_data = {"value": "new_value"}

        for setting in sensitive_settings:
            response = test_client.post(f"/admin/config/{setting}", json=request_data)
            assert response.status_code == 400
            assert "Cannot modify sensitive settings via API" in response.json()["detail"]

    def test_update_config_setting_error(self, test_client):
        """Test error handling during setting update."""
        with patch('src.api.v1.admin.endpoints.config.settings') as mock_config:
            mock_config.exists.return_value = True
            mock_config.set.side_effect = Exception("Test error")

            response = test_client.post("/admin/config/test_setting", json={"value": "new_value"})

            assert response.status_code == 500
            assert "Failed to update setting" in response.json()["detail"]

    def test_get_config_setting_success(self, test_client):
        """Test successful retrieval of a specific setting."""
        test_setting = "test_setting"
        expected_value = "test_value"

        with patch('src.api.v1.admin.endpoints.config.settings') as mock_config:
            mock_config.exists.return_value = True
            mock_config.get.return_value = expected_value

            response = test_client.get(f"/admin/config/{test_setting}")

            assert response.status_code == 200
            assert response.json() == {"key": test_setting, "value": expected_value}

    def test_get_sensitive_setting_blocked(self, test_client):
        """Test blocking access to sensitive settings."""
        sensitive_settings = ["secret_key", "api_key", "password", "token"]

        for setting in sensitive_settings:
            with patch('src.api.v1.admin.endpoints.config.settings') as mock_config:
                mock_config.exists.return_value = True  # Setting exists but is sensitive
                response = test_client.get(f"/admin/config/{setting}")
                assert response.status_code == 400
                assert "Cannot retrieve sensitive settings" in response.json()["detail"]

    def test_get_nonexistent_setting(self, test_client):
        """Test retrieval of non-existent setting."""
        with patch('src.api.v1.admin.endpoints.config.settings') as mock_config:
            mock_config.exists.return_value = False

            response = test_client.get("/admin/config/nonexistent_setting")

            assert response.status_code == 404
            assert "Setting not found" in response.json()["detail"]

    def test_get_config_setting_error(self, test_client):
        """Test error handling during specific setting retrieval."""
        with patch('src.api.v1.admin.endpoints.config.settings') as mock_config:
            mock_config.exists.return_value = True
            mock_config.get.side_effect = Exception("Test error")

            response = test_client.get("/admin/config/test_setting")

            assert response.status_code == 500
            assert "Failed to retrieve setting" in response.json()["detail"]

    def test_update_nonexistent_setting(self, test_client):
        """Test update of non-existent setting."""
        with patch('src.api.v1.admin.endpoints.config.settings') as mock_config:
            mock_config.exists.return_value = False

            response = test_client.post("/admin/config/nonexistent_setting", json={"value": "new_value"})

            assert response.status_code == 404
            assert "Setting not found" in response.json()["detail"]
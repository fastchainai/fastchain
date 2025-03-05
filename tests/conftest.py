"""Configure test environment and provide shared fixtures."""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from dynaconf import Dynaconf
from fastapi.testclient import TestClient
from langchain.llms.base import BaseLLM
from openai import OpenAI
from redis import Redis

# Add the src directory to the Python path
root_dir = Path(__file__).parent.parent  
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "src"))

# Configure pytest
def pytest_configure(config):
    """Configure pytest for the test suite."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers",
        "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers",
        "smoke: mark test as smoke test"
    )
    config.addinivalue_line(
        "markers",
        "performance: mark test as performance test"
    )

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    mock = MagicMock(spec=OpenAI)
    return mock

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock = MagicMock(spec=Redis)
    return mock

@pytest.fixture
def mock_llm():
    """Mock LangChain LLM for testing."""
    mock = MagicMock(spec=BaseLLM)
    return mock

@pytest.fixture
def test_config():
    """Create a test configuration using Dynaconf."""
    return Dynaconf(
        settings_files=["tests/settings.test.toml"],
        environments=True,
        env="test",
    )

@pytest.fixture
def test_client():
    """Create a FastAPI TestClient instance."""
    from fastapi import FastAPI
    app = FastAPI()
    return TestClient(app)

@pytest.fixture
def base_test_data():
    """Provide base test data used across multiple tests."""
    return {
        "test_agent_metadata": {
            "agent_name": "test_agent",
            "version": "1.0.0",
            "capabilities": ["test"],
            "status": "active"
        },
        "test_task": {
            "task_id": "test-123",
            "type": "test",
            "payload": {"key": "value"}
        }
    }

@pytest.fixture
def mock_registry():
    """Mock the Agent Registry for testing."""
    class MockRegistry:
        def __init__(self):
            self.agents = {}

        def register_agent(self, name, metadata):
            self.agents[name] = metadata

        def update_agent(self, name, metadata):
            if name in self.agents:
                self.agents[name].update(metadata)

        def get_agent(self, name):
            return self.agents.get(name)

    return MockRegistry()
"""Unit tests for the tool discovery system."""
import pytest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
import json
import os
from src.tools.discovery import ToolDiscovery
from src.tools.base import Tool, ToolRegistry

class MockTool(Tool):
    """Mock tool for testing."""
    name = "mock_tool"
    description = "A mock tool for testing"
    required_params = ["param1"]

    def _execute_impl(self, params, context):
        return {"result": "success"}

@pytest.fixture
def mock_registry():
    """Create a mock tool registry."""
    return MagicMock(spec=ToolRegistry)

@pytest.fixture
def tool_discovery(mock_registry):
    """Create a ToolDiscovery instance with mocked files."""
    with patch('builtins.open', mock_open()), \
         patch('os.path.exists', return_value=False):
        discovery = ToolDiscovery(registry=mock_registry)
        return discovery

class TestToolDiscovery:
    """Test suite for the ToolDiscovery system."""

    def test_initialization(self, tool_discovery):
        """Test ToolDiscovery initialization."""
        assert isinstance(tool_discovery.performance_history, dict)
        assert isinstance(tool_discovery.tool_patterns, dict)
        assert "tools" in tool_discovery.performance_history
        assert "patterns" in tool_discovery.tool_patterns

    def test_load_existing_performance_history(self, mock_registry):
        """Test loading existing performance history."""
        mock_history = {
            "tools": {
                "mock_tool": {
                    "success_count": 5,
                    "total_executions": 10,
                    "avg_execution_time": 0.5
                }
            },
            "last_updated": "2025-03-03T00:00:00"
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_history))), \
             patch('os.path.exists', return_value=True):
            discovery = ToolDiscovery(registry=mock_registry)
            assert discovery.performance_history["tools"]["mock_tool"]["success_count"] == 5

    def test_load_existing_tool_patterns(self, mock_registry):
        """Test loading existing tool patterns."""
        mock_patterns = {
            "patterns": [
                {
                    "tool_name": "mock_tool",
                    "intent": "test_intent",
                    "entities_present": ["entity1"]
                }
            ],
            "last_updated": "2025-03-03T00:00:00"
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_patterns))), \
             patch('os.path.exists', return_value=True):
            discovery = ToolDiscovery(registry=mock_registry)
            assert len(discovery.tool_patterns["patterns"]) == 1

    def test_save_performance_history(self, tool_discovery):
        """Test saving performance history."""
        mock_file = mock_open()
        with patch('builtins.open', mock_file), \
             patch('os.makedirs'):
            tool_discovery._save_performance_history()
            mock_file.assert_called_once_with("data/tool_performance_history.json", 'w')

    def test_save_tool_patterns(self, tool_discovery):
        """Test saving tool patterns."""
        mock_file = mock_open()
        with patch('builtins.open', mock_file), \
             patch('os.makedirs'):
            tool_discovery._save_tool_patterns()
            mock_file.assert_called_once_with("data/tool_patterns.json", 'w')

    def test_record_tool_execution(self, tool_discovery):
        """Test recording tool execution results."""
        context = {
            "intent": "test_intent",
            "entities": {"entity1": "value1"},
            "metadata": {"key1": "value1"}
        }
        
        tool_discovery.record_tool_execution(
            tool_name="mock_tool",
            context=context,
            success=True,
            execution_time=0.5
        )
        
        tool_stats = tool_discovery.performance_history["tools"]["mock_tool"]
        assert tool_stats["success_count"] == 1
        assert tool_stats["total_executions"] == 1
        assert tool_stats["avg_execution_time"] == 0.5
        assert "test_intent" in tool_stats["intent_patterns"]

    def test_record_failed_execution(self, tool_discovery):
        """Test recording failed tool execution."""
        context = {"intent": "test_intent"}
        
        tool_discovery.record_tool_execution(
            tool_name="mock_tool",
            context=context,
            success=False,
            execution_time=0.5
        )
        
        tool_stats = tool_discovery.performance_history["tools"]["mock_tool"]
        assert tool_stats["success_count"] == 0
        assert tool_stats["total_executions"] == 1

    def test_learn_tool_pattern(self, tool_discovery):
        """Test learning new tool pattern."""
        context = {
            "intent": "test_intent",
            "entities": {"entity1": "value1"},
            "metadata": {"key1": "value1"}
        }
        
        tool_discovery._learn_tool_pattern("mock_tool", context)
        
        patterns = tool_discovery.tool_patterns["patterns"]
        assert len(patterns) == 1
        assert patterns[0]["tool_name"] == "mock_tool"
        assert patterns[0]["intent"] == "test_intent"
        assert "entity1" in patterns[0]["entities_present"]

    def test_suggest_tool_chain(self, tool_discovery):
        """Test suggesting tool chain based on patterns."""
        # Record some executions first
        context = {"intent": "test_intent"}
        tool_discovery.record_tool_execution(
            tool_name="mock_tool",
            context=context,
            success=True,
            execution_time=0.5
        )
        
        suggested_chain = tool_discovery.suggest_tool_chain(
            intent="test_intent",
            context={"entities": {}}
        )
        
        assert len(suggested_chain) > 0
        assert "mock_tool" in suggested_chain

    def test_get_tool_analytics(self, tool_discovery):
        """Test getting tool analytics."""
        # Record some executions
        context = {"intent": "test_intent"}
        tool_discovery.record_tool_execution(
            tool_name="mock_tool",
            context=context,
            success=True,
            execution_time=0.5
        )
        
        analytics = tool_discovery.get_tool_analytics()
        
        assert "tools" in analytics
        assert "mock_tool" in analytics["tools"]
        tool_stats = analytics["tools"]["mock_tool"]
        assert tool_stats["success_rate"] == 1.0
        assert tool_stats["avg_execution_time"] == 0.5
        assert tool_stats["total_executions"] == 1
        assert tool_stats["intent_coverage"] == 1

    def test_error_handling_missing_files(self, mock_registry):
        """Test error handling when files are missing."""
        with patch('os.path.exists', return_value=False):
            discovery = ToolDiscovery(registry=mock_registry)
            assert discovery.performance_history["tools"] == {}
            assert discovery.tool_patterns["patterns"] == []

    def test_error_handling_invalid_json(self, mock_registry):
        """Test error handling with invalid JSON files."""
        with patch('builtins.open', mock_open(read_data="invalid json")), \
             patch('os.path.exists', return_value=True):
            discovery = ToolDiscovery(registry=mock_registry)
            assert discovery.performance_history["tools"] == {}
            assert discovery.tool_patterns["patterns"] == []

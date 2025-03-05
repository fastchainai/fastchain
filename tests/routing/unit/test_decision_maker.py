"""Unit tests for the Decision Making Module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.routing.decision_maker import DecisionMaker
from src.agents.registry import AgentRegistry

@pytest.fixture
def mock_registry():
    """Create a mock registry for testing."""
    mock_reg = MagicMock(spec=AgentRegistry)
    mock_reg.get_all_agents.return_value = {
        "agent1": {
            "capabilities": ["intent"],
            "status": "active",
            "performance": {"success_rate": 0.95},
            "load": 0.3
        },
        "agent2": {
            "capabilities": ["intent", "chat"],
            "status": "active",
            "performance": {"success_rate": 0.85},
            "load": 0.1
        }
    }
    return mock_reg

@pytest.fixture
def mock_agent_registry(mock_registry):
    """Mock the AgentRegistry.get_instance() method."""
    with patch.object(AgentRegistry, 'get_instance', return_value=mock_registry):
        yield mock_registry

class TestDecisionMaker:
    """Test suite for the Decision Making Module."""

    def test_initialization(self, mock_agent_registry):
        """Test DecisionMaker initialization with default weights."""
        dm = DecisionMaker()
        assert dm.weight_performance == 0.6
        assert dm.weight_load == 0.4
        assert dm.registry == mock_agent_registry

    def test_get_load_metrics(self, mock_agent_registry):
        """Test load metrics calculation."""
        dm = DecisionMaker()
        load_metrics = dm.get_load_metrics()
        assert isinstance(load_metrics, dict)
        assert "agent1" in load_metrics
        assert "agent2" in load_metrics
        assert 0 <= load_metrics["agent1"] <= 1.0
        assert 0 <= load_metrics["agent2"] <= 1.0

    def test_get_performance_metrics(self, mock_agent_registry):
        """Test performance metrics calculation."""
        dm = DecisionMaker()
        perf_metrics = dm.get_performance_metrics()
        assert isinstance(perf_metrics, dict)
        assert "agent1" in perf_metrics
        assert "agent2" in perf_metrics
        assert 0 <= perf_metrics["agent1"] <= 1.0
        assert 0 <= perf_metrics["agent2"] <= 1.0

    @pytest.mark.parametrize("capability,expected_agent", [
        ("intent", "agent2"),  # agent2 wins due to better combined score (0.85*0.6 + 0.9*0.4 > 0.95*0.6 + 0.7*0.4)
        ("chat", "agent2"),    # only agent2 has chat capability
    ])
    def test_route_task(self, mock_agent_registry, capability, expected_agent):
        """Test task routing based on capabilities and metrics."""
        dm = DecisionMaker()
        selected_agent = dm.route_task(capability)
        assert selected_agent == expected_agent

    def test_route_task_no_capable_agents(self, mock_agent_registry):
        """Test routing when no agents have the required capability."""
        mock_agent_registry.get_all_agents.return_value = {}
        dm = DecisionMaker()
        with pytest.raises(RuntimeError, match="No agents found with capability"):
            dm.route_task("unknown_capability")

    def test_route_task_inactive_agents(self, mock_agent_registry):
        """Test routing excludes inactive agents."""
        mock_agent_registry.get_all_agents.return_value = {
            "agent1": {
                "capabilities": ["intent"],
                "status": "inactive",
                "performance": {"success_rate": 0.95},
                "load": 0.3
            }
        }
        dm = DecisionMaker()
        with pytest.raises(RuntimeError, match="No active agents found with capability"):
            dm.route_task("intent")

    def test_route_task_handles_missing_metrics(self, mock_agent_registry):
        """Test handling of agents with missing performance or load metrics."""
        mock_agent_registry.get_all_agents.return_value = {
            "agent1": {
                "capabilities": ["intent"],
                "status": "active"
                # Missing metrics
            }
        }
        dm = DecisionMaker()
        with pytest.raises(RuntimeError, match="Invalid metrics for agent"):
            dm.route_task("intent")

    def test_route_task_updates_metrics(self, mock_agent_registry):
        """Test that routing a task triggers metric updates."""
        dm = DecisionMaker()
        with patch.object(mock_agent_registry, 'update_agent') as mock_update:
            dm.route_task("intent")
            mock_update.assert_called_once()

    @pytest.mark.parametrize("test_case", [
        {
            "agent_id": "agent1",
            "load_metrics": {"agent1": 0.3},
            "performance_metrics": {"agent1": 0.9},
            "expected_score": 0.82  # (0.6 * 0.9) + (0.4 * (1 - 0.3))
        },
        {
            "agent_id": "agent2",
            "load_metrics": {"agent2": 0.8},
            "performance_metrics": {"agent2": 0.7},
            "expected_score": 0.50  # (0.6 * 0.7) + (0.4 * (1 - 0.8))
        },
        {
            "agent_id": "agent3",
            "load_metrics": {"agent3": 0.1},
            "performance_metrics": {"agent3": 0.5},
            "expected_score": 0.66  # (0.6 * 0.5) + (0.4 * (1 - 0.1))
        }
    ])
    def test_score_calculation(self, mock_agent_registry, test_case):
        """Test the agent scoring calculation with different metrics."""
        dm = DecisionMaker()
        score = dm.calculate_agent_score(
            test_case["agent_id"],
            test_case["load_metrics"],
            test_case["performance_metrics"]
        )
        assert abs(score - test_case["expected_score"]) < 0.01  # Allow small floating point differences

    def test_route_task_with_capability_weights(self, mock_agent_registry):
        """Test routing with capability-specific weights."""
        dm = DecisionMaker()

        # Test intent routing where agent1 has better performance
        mock_agent_registry.get_all_agents.return_value = {
            "agent1": {
                "capabilities": ["intent"],
                "status": "active",
                "performance": {"success_rate": 0.95},
                "load": 0.3
            },
            "agent2": {
                "capabilities": ["intent", "chat"],
                "status": "active",
                "performance": {"success_rate": 0.85},
                "load": 0.1
            }
        }

        selected_agent = dm.route_task("intent", performance_weight=0.8, load_weight=0.2)
        assert selected_agent == "agent1"  # Should prefer agent1 due to better performance

    def test_route_task_with_threshold(self, mock_agent_registry):
        """Test routing with minimum performance threshold."""
        dm = DecisionMaker()
        mock_agent_registry.get_all_agents.return_value = {
            "agent1": {
                "capabilities": ["intent"],
                "status": "active",
                "performance": {"success_rate": 0.95},
                "load": 0.3
            },
            "agent2": {
                "capabilities": ["intent"],
                "status": "active",
                "performance": {"success_rate": 0.85},
                "load": 0.1
            }
        }

        # Only agent1 meets threshold
        selected_agent = dm.route_task("intent", min_performance=0.90)
        assert selected_agent == "agent1"

        # No agent meets higher threshold
        with pytest.raises(RuntimeError, match="No agents meet minimum performance threshold"):
            dm.route_task("intent", min_performance=0.99)

    def test_route_task_with_custom_weights(self, mock_agent_registry):
        """Test routing with custom performance/load weights."""
        dm = DecisionMaker()

        # Test with load weighted more heavily
        selected_agent = dm.route_task("intent", performance_weight=0.3, load_weight=0.7)
        assert selected_agent == "agent2"  # Should prefer agent2 due to lower load
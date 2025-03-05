"""Unit tests for the Intent Agent Task Engine."""
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from pydantic import BaseModel, Field, ValidationError
from src.agents.intent_agent.task_engine import TaskEngine, IntentClassification

@pytest.fixture
def mock_classifier():
    """Create a mock classifier."""
    mock = Mock()
    mock.classify_intent = AsyncMock(return_value={
        'intent': 'weather_query',
        'confidence': 0.95,
        'action_required': True,
        'explanation': 'Weather related query detected'
    })
    return mock

@pytest.fixture
def mock_extractor():
    """Create a mock entity extractor."""
    mock = Mock()
    mock.extract_entities = AsyncMock(return_value={'location': ['San Francisco']})
    return mock

@pytest_asyncio.fixture
async def task_engine(mock_classifier, mock_extractor):
    """Create a TaskEngine instance for testing with mocked dependencies."""
    with patch('src.agents.intent_agent.task_engine.IntentClassifierModel', return_value=mock_classifier), \
         patch('src.agents.intent_agent.task_engine.EntityExtractorModel', return_value=mock_extractor):
        engine = TaskEngine()
        yield engine

class TestTaskEngine:
    """Test suite for TaskEngine class."""

    def test_initialization(self, mock_classifier, mock_extractor):
        """Test TaskEngine initialization."""
        with patch('src.agents.intent_agent.task_engine.IntentClassifierModel', return_value=mock_classifier), \
             patch('src.agents.intent_agent.task_engine.EntityExtractorModel', return_value=mock_extractor):
            engine = TaskEngine()
            assert engine.classifier is not None
            assert engine.extractor is not None

    def test_initialization_failure(self):
        """Test TaskEngine initialization failure."""
        with patch('src.agents.intent_agent.task_engine.IntentClassifierModel', 
                  side_effect=Exception("Failed to load model")), \
             pytest.raises(RuntimeError) as exc_info:
            TaskEngine()
        assert "Failed to initialize task engine" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_query_success(self, task_engine):
        """Test successful query processing."""
        # Execute test
        result = await task_engine.process_query("What's the weather like?")

        # Verify results
        assert result['intent'] == {
            'name': 'weather_query',
            'type': 'user_intent'
        }
        assert result['confidence'] == 0.95
        assert result['requires_action'] is True
        assert isinstance(result['metadata']['processing_timestamp'], str)
        assert result['metadata'].get('explanation') == 'Weather related query detected'
        assert result['entities'] == {'location': ['San Francisco']}

    @pytest.mark.asyncio
    async def test_process_query_failure(self, task_engine, mock_classifier):
        """Test query processing failure."""
        mock_classifier.classify_intent = AsyncMock(side_effect=Exception("Classification failed"))

        with pytest.raises(RuntimeError) as exc_info:
            await task_engine.process_query("Test query")

        assert "Failed to process query" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_query_empty_query(self, task_engine):
        """Test processing empty query string."""
        with pytest.raises(ValueError) as exc_info:
            await task_engine.process_query("")
        assert "Query cannot be empty" in str(exc_info.value)

def test_intent_classification_model():
    """Test IntentClassification Pydantic model."""
    data = {
        'intent_name': 'test_intent',
        'confidence': 0.95,
        'entities': {'location': ['New York']},
        'action_required': True
    }

    classification = IntentClassification(**data)

    assert classification.intent_name == 'test_intent'
    assert classification.confidence == 0.95
    assert classification.entities == {'location': ['New York']}
    assert classification.action_required is True

def test_intent_classification_model_validation():
    """Test IntentClassification model validation."""
    # Test invalid confidence value
    with pytest.raises(ValidationError) as exc_info:
        IntentClassification(
            intent_name="test",
            confidence=1.5,  # Should be between 0 and 1
            entities={},
            action_required=True
        )
    assert "Input should be less than or equal to 1" in str(exc_info.value)

    # Test invalid entities format
    with pytest.raises(ValidationError) as exc_info:
        IntentClassification(
            intent_name="test",
            confidence=0.5,
            entities="invalid",  # Should be a dict
            action_required=True
        )
    assert "Input should be a valid dictionary" in str(exc_info.value)
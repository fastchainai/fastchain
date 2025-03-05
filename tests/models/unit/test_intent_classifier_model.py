"""Unit tests for the Intent Classifier Model."""
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import numpy as np

from src.models.intent_classifier_model import IntentClassifierModel
from langchain_core.prompts import PromptTemplate

@pytest.fixture
async def mock_embeddings():
    """Create a mock OpenAI embeddings."""
    mock = AsyncMock()
    mock.embed_query = AsyncMock(return_value=np.array([0.1, 0.2, 0.3]))
    return mock

@pytest.fixture
async def mock_llm():
    """Create a mock OpenAI LLM."""
    mock = AsyncMock()
    mock.apredict = AsyncMock(return_value="Intent: weather\nConfidence: 0.95\nExplanation: Weather related query")
    mock.predict = Mock(return_value="Intent: weather\nConfidence: 0.95\nExplanation: Weather related query")
    return mock

@pytest.fixture
async def intent_classifier(mock_embeddings, mock_llm):
    """Create an IntentClassifierModel instance with mocked dependencies."""
    with patch('src.models.intent_classifier_model.OpenAIEmbeddings', return_value=mock_embeddings), \
         patch('src.models.intent_classifier_model.OpenAI', return_value=mock_llm), \
         patch('src.models.intent_classifier_model.PromptTemplate', return_value=Mock(spec=PromptTemplate)) as mock_prompt:
        mock_prompt.return_value.format = Mock(return_value="formatted prompt")
        classifier = IntentClassifierModel()
        classifier._patterns = {
            "patterns": [],
            "last_updated": datetime.now().isoformat()
        }
        return classifier

class TestIntentClassifierModel:
    """Test suite for IntentClassifierModel."""

    @pytest.mark.asyncio
    async def test_initialization(self, intent_classifier):
        """Test model initialization."""
        assert intent_classifier is not None
        assert intent_classifier._embeddings is not None
        assert isinstance(intent_classifier._patterns, dict)
        assert "patterns" in intent_classifier._patterns
        assert "last_updated" in intent_classifier._patterns

    def test_initialization_failure(self):
        """Test initialization failure handling."""
        with patch('src.models.intent_classifier_model.OpenAIEmbeddings',
                  side_effect=Exception("Failed to initialize embeddings")), \
             pytest.raises(RuntimeError) as exc_info:
            IntentClassifierModel()
        assert "Failed to initialize IntentClassifierModel" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_classify_intent_success(self, intent_classifier, mock_llm):
        """Test successful intent classification."""
        # Test the async prediction path
        result = await intent_classifier.classify_intent("What's the weather like?")

        assert isinstance(result, dict)
        assert result["intent"] == "weather"
        assert result["confidence"] == "0.95"
        assert "explanation" in result

        # Test the sync prediction path
        mock_llm.apredict = AsyncMock(side_effect=AttributeError)
        result = await intent_classifier.classify_intent("What's the weather like?")

        assert isinstance(result, dict)
        assert result["intent"] == "weather"
        assert result["confidence"] == "0.95"

    @pytest.mark.asyncio
    async def test_classify_intent_with_pattern_matching(self, intent_classifier, mock_embeddings):
        """Test intent classification with pattern matching."""
        # Set up test patterns
        test_pattern = {
            "query_pattern": "weather forecast",
            "intent": "weather",
            "category": "weather",
            "embedding": np.array([0.1, 0.2, 0.3]),
            "learned_at": datetime.now().isoformat(),
            "success_count": 1
        }
        intent_classifier._patterns["patterns"] = [test_pattern]

        mock_embeddings.embed_query.return_value = np.array([0.1, 0.2, 0.3])

        result = await intent_classifier.classify_intent("What's the weather forecast?")

        assert result["intent"] == "weather"
        assert result["has_pattern_match"] is True
        assert len(result["similar_patterns"]) > 0

    @pytest.mark.asyncio
    async def test_classify_intent_failure(self, intent_classifier, mock_llm):
        """Test intent classification failure handling."""
        mock_llm.apredict.side_effect = Exception("Classification failed")
        mock_llm.predict.side_effect = Exception("Classification failed")

        result = await intent_classifier.classify_intent("Test query")

        assert result["intent"] == "error"
        assert result["confidence"] == 0.0
        assert "Classification error" in result["explanation"]

    @pytest.mark.asyncio
    async def test_learn_from_feedback_success(self, intent_classifier, mock_embeddings):
        """Test successful pattern learning from feedback."""
        test_text = "What's the weather like?"
        test_result = {
            "intent": "weather",
            "new_pattern": "yes",
            "category": "weather_query"
        }

        await intent_classifier.learn_from_feedback(test_text, test_result, True)

        assert len(intent_classifier._patterns["patterns"]) > 0
        latest_pattern = intent_classifier._patterns["patterns"][-1]
        assert latest_pattern["query_pattern"] == test_text
        assert latest_pattern["intent"] == "weather"

    @pytest.mark.asyncio
    async def test_validate_model(self, intent_classifier):
        """Test model validation."""
        assert intent_classifier.validate_model() is True

        # Test validation with missing embeddings
        intent_classifier._embeddings = None
        assert intent_classifier.validate_model() is False

    @pytest.mark.asyncio
    async def test_save_and_load_patterns(self, intent_classifier, tmp_path):
        """Test pattern persistence."""
        # Setup test pattern
        test_pattern = {
            "patterns": [{
                "query_pattern": "test query",
                "intent": "test_intent",
                "category": "test",
                "embedding": [0.1, 0.2, 0.3],
                "learned_at": datetime.now().isoformat(),
                "success_count": 1
            }],
            "last_updated": datetime.now().isoformat()
        }

        # Set patterns and test file path
        intent_classifier._patterns = test_pattern
        test_file = tmp_path / "test_patterns.json"
        intent_classifier.patterns_file = str(test_file)

        # Test save
        await intent_classifier._save_patterns()
        assert test_file.exists()

        # Test load
        with open(test_file, 'r') as f:
            loaded_patterns = json.load(f)
        assert loaded_patterns["patterns"][0]["query_pattern"] == "test query"
        assert loaded_patterns["patterns"][0]["intent"] == "test_intent"
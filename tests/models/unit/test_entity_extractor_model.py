"""Unit tests for the Entity Extractor Model."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from src.models.entity_extractor_model import EntityExtractorModel
from langchain_core.prompts import PromptTemplate

@pytest.fixture
async def mock_llm():
    """Create a mock OpenAI LLM."""
    mock = AsyncMock()
    mock.apredict = AsyncMock(return_value='{"location": ["San Francisco"], "date": ["tomorrow"], "person": ["John"]}')
    mock.predict = Mock(return_value='{"location": ["San Francisco"], "date": ["tomorrow"], "person": ["John"]}')
    return mock

@pytest.fixture
def mock_spacy_entity():
    """Create a mock spaCy entity."""
    entity = MagicMock()
    entity.text = "San Francisco"
    entity.label_ = "GPE"
    return entity

@pytest.fixture
def mock_spacy_doc(mock_spacy_entity):
    """Create a mock spaCy Doc with entities."""
    doc = MagicMock()
    doc.ents = [mock_spacy_entity]
    return doc

@pytest.fixture
def mock_nlp(mock_spacy_doc):
    """Create a mock spaCy NLP."""
    nlp = MagicMock()
    nlp.return_value = mock_spacy_doc
    return nlp

@pytest.fixture
async def entity_extractor(mock_llm, mock_nlp):
    """Create an EntityExtractorModel instance with mocked dependencies."""
    with patch('src.models.entity_extractor_model.OpenAI', return_value=mock_llm), \
         patch('src.models.entity_extractor_model.spacy.load', return_value=mock_nlp), \
         patch('src.models.entity_extractor_model.PromptTemplate', return_value=Mock(spec=PromptTemplate)) as mock_prompt:
        mock_prompt.return_value.format = Mock(return_value="formatted prompt")
        extractor = EntityExtractorModel()
        extractor._nlp = mock_nlp
        return extractor

class TestEntityExtractorModel:
    """Test suite for EntityExtractorModel."""

    @pytest.mark.asyncio
    async def test_initialization(self, entity_extractor):
        """Test model initialization."""
        assert entity_extractor is not None
        assert entity_extractor._nlp is not None
        assert entity_extractor._prompt is not None

    def test_initialization_failure(self):
        """Test initialization failure handling."""
        with patch('src.models.entity_extractor_model.OpenAI',
                  side_effect=Exception("Failed to initialize LLM")), \
             pytest.raises(RuntimeError) as exc_info:
            EntityExtractorModel()
        assert "Failed to initialize entity extractor" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_entities_success(self, entity_extractor, mock_llm, mock_spacy_doc):
        """Test successful entity extraction."""
        # Setup mock NLP to return test entities
        entity_extractor._nlp.return_value = mock_spacy_doc

        result = await entity_extractor.extract_entities("Meeting in San Francisco tomorrow with John")

        assert isinstance(result, dict)
        assert "location" in result
        assert "San Francisco" in result["location"]
        assert "date" in result
        assert "tomorrow" in result["date"]
        assert "person" in result
        assert "John" in result["person"]

    @pytest.mark.asyncio
    async def test_extract_entities_no_entities(self, entity_extractor, mock_llm):
        """Test extraction with no entities found."""
        # Set up empty entities
        mock_doc = MagicMock()
        mock_doc.ents = []
        entity_extractor._nlp.return_value = mock_doc

        mock_llm.apredict.return_value = "{}"
        mock_llm.predict.return_value = "{}"

        result = await entity_extractor.extract_entities("Hello world")
        assert isinstance(result, dict)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_extract_entities_failure(self, entity_extractor, mock_llm):
        """Test entity extraction failure handling."""
        entity_extractor._nlp.side_effect = Exception("NLP processing failed")
        mock_llm.apredict.side_effect = Exception("LLM extraction failed")
        mock_llm.predict.side_effect = Exception("LLM extraction failed")

        result = await entity_extractor.extract_entities("Test text")
        assert isinstance(result, dict)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_extract_entities_invalid_response(self, entity_extractor, mock_llm):
        """Test handling of invalid LLM response format."""
        mock_llm.apredict.return_value = "Invalid JSON"
        mock_llm.predict.return_value = "Invalid JSON"

        result = await entity_extractor.extract_entities("Test text")
        assert isinstance(result, dict)
        assert all(isinstance(v, list) for v in result.values())

    @pytest.mark.asyncio
    async def test_extract_entities_with_context(self, entity_extractor, mock_llm, mock_spacy_doc):
        """Test entity extraction with additional context."""
        # Setup mock NLP to return test entities
        entity_extractor._nlp.return_value = mock_spacy_doc

        context = {"previous_entities": {"location": ["New York"]}}
        mock_llm.apredict.return_value = '{"location": ["San Francisco", "New York"], "date": ["tomorrow"]}'

        result = await entity_extractor.extract_entities(
            "Meeting in San Francisco tomorrow, then flying to New York",
            context=context
        )

        assert isinstance(result, dict)
        assert "location" in result
        assert "San Francisco" in result["location"]
        assert "New York" in result["location"]
        assert "date" in result
        assert "tomorrow" in result["date"]

    @pytest.mark.parametrize("input_text", [
        "",
        "   ",
        None
    ])
    @pytest.mark.asyncio
    async def test_extract_entities_empty_input(self, entity_extractor, input_text):
        """Test extraction with empty or invalid input."""
        with pytest.raises(ValueError) as exc_info:
            await entity_extractor.extract_entities(input_text)
        assert "Input text cannot be empty" in str(exc_info.value)
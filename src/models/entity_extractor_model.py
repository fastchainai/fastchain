"""Entity extraction model implementation."""
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import re
import numpy as np
import spacy
from spacy.language import Language
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from .langchain_model import LangChainModel
from src.utils.logging import Logging

# Initialize logger
logger = Logging(__name__)

class EntityExtractorModel(LangChainModel):
    """
    Entity extraction model with spaCy integration for enhanced entity recognition.
    """
    _nlp: Optional[Language] = None

    def __init__(self, **data):
        """Initialize the entity extractor."""
        super().__init__(**data)
        self._initialize_components()

    def _initialize_components(self):
        """Initialize model components."""
        try:
            # Initialize spaCy
            self._nlp = spacy.load("en_core_web_sm")

            # Set up entity extraction chain
            self._setup_extraction_chain()

            logger.info("EntityExtractorModel initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize entity extractor: {e}")
            raise RuntimeError(f"Failed to initialize entity extractor: {str(e)}")

    def _setup_extraction_chain(self):
        """Set up the entity extraction chain."""
        extraction_template = """
        Extract entities from the following text. Focus on:
        - Dates and times
        - Locations
        - Numbers and quantities
        - Organizations
        - People
        - Custom entities (products, services, etc.)

        Text: {input_text}

        Format the response as a JSON with these categories.
        Each category should be singular (e.g., "location" not "locations").
        """

        self._prompt = PromptTemplate(
            input_variables=["input_text"],
            template=extraction_template
        )
        self._llm = OpenAI(temperature=0)

    async def extract_entities(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
        """
        Extract entities using both spaCy and LLM for comprehensive coverage.

        Args:
            text: Input text to extract entities from
            context: Optional context information to enhance extraction

        Returns:
            Dictionary of extracted entities by category
        """
        if not text or not text.strip():
            logger.error("Empty input text received")
            raise ValueError("Input text cannot be empty")

        try:
            # Get spaCy entities
            doc = self._nlp(text)

            entities = {}

            # Extract named entities using spaCy
            for ent in doc.ents:
                category = self._map_spacy_entity(ent.label_)
                if category:
                    if category not in entities:
                        entities[category] = []
                    if ent.text not in entities[category]:
                        entities[category].append(ent.text)

            # Additional date extraction using regex
            dates = self._extract_dates(text)
            if dates:
                if "date" not in entities:
                    entities["date"] = []
                entities["date"].extend(dates)

            # Get enhanced entities from LLM
            try:
                llm_inputs = {"input_text": text}
                if context:
                    llm_inputs.update(context)

                result = await self._llm.apredict(self._prompt.format(**llm_inputs))
                enhanced_entities = json.loads(result)

                # Merge LLM results with spaCy results
                for category, values in enhanced_entities.items():
                    if isinstance(values, list):
                        category = category.lower()
                        if category not in entities:
                            entities[category] = []
                        entities[category].extend([v for v in values if v not in entities[category]])

            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Error in LLM extraction: {e}")

            # Remove any empty categories
            return {k: sorted(list(set(v))) for k, v in entities.items() if v}

        except Exception as e:
            logger.error(f"Error in entity extraction: {e}")
            return {}

    def _map_spacy_entity(self, label: str) -> Optional[str]:
        """Map spaCy entity labels to our standardized categories."""
        mapping = {
            'DATE': 'date',
            'TIME': 'date',
            'GPE': 'location',
            'LOC': 'location',
            'CARDINAL': 'number',
            'MONEY': 'number',
            'QUANTITY': 'number',
            'ORG': 'organization',
            'PERSON': 'person',
            'PRODUCT': 'custom',
        }
        return mapping.get(label)

    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates using regex patterns."""
        date_patterns = [
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}',
            r'\d{1,2}\s(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}'
        ]

        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        return list(set(dates))

    def validate_model(self) -> bool:
        """Validate model configuration."""
        return super().validate_model() and self._nlp is not None and self._llm is not None and self._prompt is not None
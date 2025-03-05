"""Intent classification model implementation."""
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from .langchain_model import LangChainModel
from src.utils.logging import Logging

# Initialize logger
logger = Logging(__name__)

class IntentClassifierModel(LangChainModel):
    """
    Intent classification model with pattern learning capabilities.
    """
    _embeddings: Optional[OpenAIEmbeddings] = None
    _patterns: Dict[str, Any] = {"patterns": [], "last_updated": None}
    patterns_file: str = "data/learned_patterns.json"

    def __init__(self, **data):
        """Initialize the intent classifier."""
        super().__init__(**data)
        self._initialize_components()

    def _initialize_components(self):
        """Initialize model components."""
        try:
            # Set up embeddings
            self._embeddings = OpenAIEmbeddings()

            # Load existing patterns
            self._load_patterns()

            # Set up classification chain
            self._setup_classification_chain()

            logger.info("IntentClassifierModel initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize IntentClassifierModel: {str(e)}")
            raise RuntimeError(f"Failed to initialize IntentClassifierModel: {str(e)}")

    def _setup_classification_chain(self):
        """Set up the intent classification chain."""
        intent_template = """
        Analyze the following user query and determine the primary intent.
        Consider both standard intents and any similar patterns we've seen before.

        Previous similar patterns:
        {patterns}

        User Query: {input_text}

        Output format:
        Intent: <intent>
        Category: <category>
        Confidence: <score between 0.0 and 1.0>
        Explanation: <brief explanation>
        New Pattern: <yes/no>
        Pattern Description: <if new pattern, describe it>
        """

        self._prompt = PromptTemplate(
            input_variables=["input_text", "patterns"],
            template=intent_template
        )
        self._llm = OpenAI(temperature=0)

    async def _load_patterns(self):
        """Load learned patterns from storage."""
        try:
            if os.path.exists(self.patterns_file):
                with open(self.patterns_file, 'r') as f:
                    self._patterns = json.load(f)
            else:
                self._patterns = {
                    "patterns": [],
                    "last_updated": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")

    async def _save_patterns(self):
        """Save patterns to storage."""
        try:
            os.makedirs(os.path.dirname(self.patterns_file), exist_ok=True)
            with open(self.patterns_file, 'w') as f:
                json.dump(self._patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving patterns: {e}")

    async def _get_relevant_patterns(self, input_text: str) -> List[Dict[str, Any]]:
        """Find patterns relevant to the input text."""
        if not self._patterns["patterns"]:
            return []

        try:
            query_embedding = await self._embeddings.embed_query(input_text)
            relevant = []

            for pattern in self._patterns["patterns"]:
                if "embedding" in pattern:
                    similarity = np.dot(query_embedding, pattern["embedding"]) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(pattern["embedding"])
                    )
                    if similarity > 0.7:  # Relevance threshold
                        relevant.append(pattern)

            return relevant[:3]  # Return top 3 most relevant patterns
        except Exception as e:
            logger.error(f"Error finding relevant patterns: {e}")
            return []

    async def classify_intent(self, text: str) -> Dict[str, Any]:
        """
        Process an input query to determine intent and metadata.

        Args:
            text: The input text to classify

        Returns:
            Dict containing the classified intent and metadata
        """
        try:
            # Get relevant patterns
            relevant_patterns = await self._get_relevant_patterns(text)
            patterns_context = "\n".join([
                f"- Pattern: {p['query_pattern']}, Intent: {p['intent']}, Category: {p['category']}"
                for p in relevant_patterns
            ]) or "No relevant patterns found."

            # Get classification result
            chain_inputs = {
                "input_text": text,
                "patterns": patterns_context
            }
            try:
                result = await self._llm.apredict(self._prompt.format(**chain_inputs))
            except AttributeError:
                # Fallback for non-async LLMs
                result = self._llm.predict(self._prompt.format(**chain_inputs))

            # Parse the result
            lines = result.strip().split('\n')
            parsed_result = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    parsed_result[key.strip().lower()] = value.strip()

            # Add additional metadata
            parsed_result['similar_patterns'] = [p['query_pattern'] for p in relevant_patterns]
            parsed_result['has_pattern_match'] = bool(relevant_patterns)

            return parsed_result

        except Exception as e:
            logger.error(f"Error in intent classification: {e}")
            return {
                'intent': 'error',
                'confidence': 0.0,
                'explanation': f'Classification error: {str(e)}'
            }

    async def learn_from_feedback(self, text: str, result: Dict[str, Any], success: bool):
        """
        Learn from classification feedback.

        Args:
            text: Original input text
            result: Classification result
            success: Whether classification was successful
        """
        if success and result.get("new_pattern") == "yes":
            try:
                pattern_embedding = await self._embeddings.embed_query(text)
                new_pattern = {
                    "query_pattern": text,
                    "intent": result["intent"],
                    "category": result.get("category", "unknown"),
                    "embedding": pattern_embedding,
                    "learned_at": datetime.now().isoformat(),
                    "success_count": 1
                }
                self._patterns["patterns"].append(new_pattern)
                self._patterns["last_updated"] = datetime.now().isoformat()
                await self._save_patterns()
                logger.info(f"Learned new pattern: {new_pattern['query_pattern']}")
            except Exception as e:
                logger.error(f"Error learning new pattern: {e}")

    def validate_model(self) -> bool:
        """Validate model configuration."""
        return (super().validate_model() and 
                self._embeddings is not None and
                self._llm is not None and
                self._prompt is not None)
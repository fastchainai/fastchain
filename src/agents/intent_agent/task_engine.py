"""Task Execution Engine for Intent Agent using Langchain."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from src.models.intent_classifier_model import IntentClassifierModel
from src.models.entity_extractor_model import EntityExtractorModel
from pydantic import BaseModel, Field, confloat, validator

logger = logging.getLogger(__name__)

class IntentClassification(BaseModel):
    """Schema for intent classification output."""
    intent_name: str = Field(description="The classified intent name")
    confidence: confloat(ge=0, le=1) = Field(description="Confidence score between 0 and 1")
    entities: Dict[str, List[str]] = Field(description="Extracted entities")
    action_required: bool = Field(description="Whether this intent requires an action")

    @validator('entities')
    def validate_entities(cls, v):
        """Validate entities format."""
        if not isinstance(v, dict):
            raise ValueError("Input should be a valid dictionary")
        return v

class TaskEngine:
    """
    Implements the core processing logic for intent classification and routing
    using the IntentClassifierModel and EntityExtractorModel.
    """
    def __init__(self):
        """Initialize the task engine with necessary components."""
        try:
            logger.info("[TaskEngine] Initializing task engine")
            self.classifier = IntentClassifierModel()
            self.extractor = EntityExtractorModel()
            logger.info("[TaskEngine] Task engine initialized successfully")
        except Exception as e:
            logger.error(f"[TaskEngine] Failed to initialize task engine: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize task engine: {str(e)}")

    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query to determine intent and extract entities.

        Args:
            query: The input query string

        Returns:
            Dict containing the classified intent and extracted entities
        """
        if not query or not query.strip():
            logger.error("[TaskEngine] Empty query received")
            raise ValueError("Query cannot be empty")

        try:
            logger.info(f"[TaskEngine] Processing query: {query}")

            # Use the classifier to get intent
            result = await self.classifier.classify_intent(query)
            logger.debug(f"[TaskEngine] Raw classification result: {result}")

            # Extract entities
            entities = await self.extractor.extract_entities(query)
            logger.debug(f"[TaskEngine] Extracted entities: {entities}")

            return {
                "intent": {
                    "name": result.get('intent'),
                    "type": "user_intent"
                },
                "confidence": result.get('confidence', 0.0),
                "entities": entities,
                "requires_action": result.get('action_required', False),
                "metadata": {
                    "processing_timestamp": datetime.now().isoformat(),
                    "explanation": result.get('explanation', ''),
                    "has_pattern_match": result.get('has_pattern_match', False),
                    "similar_patterns": result.get('similar_patterns', [])
                }
            }
        except Exception as e:
            logger.error(f"[TaskEngine] Error processing query: {e}", exc_info=True)
            raise RuntimeError(f"Failed to process query: {str(e)}")
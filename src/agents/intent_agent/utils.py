"""Utility functions specific to the Intent Agent."""
from typing import Dict, Any, List
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

def format_intent_response(classification_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the intent classification result for API response.
    
    Args:
        classification_result: Raw classification output
        
    Returns:
        Formatted response dictionary
    """
    return {
        "intent": {
            "name": classification_result["intent"],
            "confidence": classification_result["confidence"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "entities": classification_result["entities"],
        "metadata": {
            "requires_action": classification_result["requires_action"],
            "processed_at": datetime.utcnow().isoformat() + "Z"
        }
    }

def validate_intent_request(query: str) -> bool:
    """
    Validate an incoming intent classification request.
    
    Args:
        query: The input query to validate
        
    Returns:
        bool indicating if the request is valid
        
    Raises:
        ValueError: If the query is invalid
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")
    if len(query.strip()) == 0:
        raise ValueError("Query cannot be empty or whitespace only")
    return True

def aggregate_entity_confidence(entities: Dict[str, List[str]], 
                             confidence_scores: Dict[str, float]) -> float:
    """
    Calculate aggregate confidence score for extracted entities.
    
    Args:
        entities: Dictionary of extracted entities
        confidence_scores: Dictionary of confidence scores per entity
        
    Returns:
        Aggregate confidence score
    """
    if not entities or not confidence_scores:
        return 0.0
        
    total_score = 0.0
    count = 0
    
    for entity_type, values in entities.items():
        if entity_type in confidence_scores:
            total_score += confidence_scores[entity_type] * len(values)
            count += len(values)
    
    return total_score / count if count > 0 else 0.0

def log_intent_processing(query: str, result: Dict[str, Any]):
    """
    Log intent processing details for monitoring and debugging.
    
    Args:
        query: The original query
        result: The processing result
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "query": query,
        "intent": result["intent"],
        "confidence": result["confidence"],
        "entity_count": len(result["entities"])
    }
    logger.info(f"Intent processing completed: {json.dumps(log_entry)}")

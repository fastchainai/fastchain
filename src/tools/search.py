"""Search tool implementation."""
from typing import Dict, Any
from .base import Tool, ToolContext
from src.utils.logging import Logging

# Initialize logger with the new centralized logging system
logger = Logging(__name__)

class SearchTool(Tool):
    name = "search"
    description = "Handles search and information-related queries"
    required_params = ["entities"]
    version = "1.0.0"
    compatible_versions = ["0.9.0"]  # For backward compatibility

    def can_handle(self, context: ToolContext) -> float:
        """Determine if this tool can handle the search or information intent."""
        intent = context.intent.lower()
        logger.debug("SearchTool evaluating intent", intent=intent, metadata=context.metadata)

        # Calculate confidence based on intent and available entities
        base_confidence = 0.0

        # Direct intent matches
        if intent == 'search':
            base_confidence = 1.0
            logger.debug("Direct intent match found", intent=intent, base_confidence=base_confidence)
        elif any(term in intent for term in ['find', 'information']):
            base_confidence = 0.95  # High confidence for information-related intents
            logger.debug("Information-related intent found", intent=intent, base_confidence=base_confidence)
        elif any(term in intent for term in ['look', 'query', 'about', 'learn', 'tell me']):
            base_confidence = 0.8
            logger.debug("Related intent keyword found", intent=intent, base_confidence=base_confidence)

        # Extract search terms from the metadata if available
        query = context.metadata.get('query', '').lower()
        if query:
            # Look for information-seeking patterns
            if any(phrase in query for phrase in ['what is', 'how to', 'tell me about', 'information about']):
                base_confidence = max(base_confidence, 0.9)
                logger.debug("Information-seeking pattern found in query", 
                           query=query, adjusted_base_confidence=base_confidence)

        # Check for chain context
        if context.chain_context:
            prev_search_results = context.chain_context.get('search_results')
            if prev_search_results:
                base_confidence *= 1.1  # Boost confidence if we have relevant previous results
                logger.debug("Boosted confidence due to chain context")

        final_confidence = min(max(base_confidence, 0.0), 1.0)
        logger.debug("Final confidence for SearchTool", confidence=final_confidence)
        return final_confidence

    def _execute_impl(self, params: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        """Execute the search with given parameters."""
        if not self.validate_params(params):
            raise ValueError("Missing required parameters")

        entities = params['entities']
        logger.info("Executing search", entities=entities)

        # Extract search terms
        query_terms = context.metadata.get('query', '').split()
        if not query_terms:
            raise ValueError("No search terms available")

        # Remove common stop words
        stop_words = {'find', 'me', 'about', 'information', 'search', 'for'}
        search_terms = [term for term in query_terms if term.lower() not in stop_words]
        logger.debug("Extracted search terms", terms=search_terms)

        # Consider chain context for enhanced search
        if context.chain_context:
            prev_results = context.chain_context.get('search_results', [])
            logger.debug("Using previous results from chain", previous_results=prev_results)
            # Enhance search terms based on previous results
            if prev_results:
                search_terms.extend([term for term in prev_results if term not in search_terms])

        # Log search context for debugging
        logger.debug("Search context", 
                    intent=context.intent,
                    confidence=context.confidence,
                    terms=search_terms)

        result = {
            'action': 'search',
            'parameters': {
                'terms': search_terms,
                'query': context.metadata.get('query', ''),
                'context': context.metadata
            },
            'status': 'completed',
            'search_results': search_terms  # For chain context
        }

        # Suggest next tools based on search results
        if any(term in search_terms for term in ['book', 'reserve', 'schedule']):
            result['next_tools'] = ['booking']

        return result
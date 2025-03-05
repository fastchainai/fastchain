"""Task Execution Engine for the Chat Agent."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

from langchain_community.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_community.chains.router import MultiRouteChain
from langchain_community.chains.router.llm_router import LLMRouterChain, RouterOutputParser
from langchain_core.memory import ConversationBufferMemory

from src.utils.logging import Logging
from src.utils.metrics import PrometheusMetrics
from src.utils.tracing import SpanContextManager

# Initialize structured logging
logger = Logging(__name__)

# Initialize metrics
task_metrics = PrometheusMetrics(
    "chat_task_engine",
    default_tags={"component": "task_engine"}
)

class ChatTaskEngine:
    """
    Implements the core processing logic for chat messages using Langchain chains.
    Handles message processing, intent classification, and task routing with advanced NLP capabilities.
    """

    def __init__(self):
        """Initialize the Chat Task Engine with advanced routing and NLP capabilities."""
        with SpanContextManager("init_chat_task_engine") as span:
            try:
                logger.info(event="task_engine_init_start")
                self.chains = {}
                self.memories = {}
                self._initialize_chains()
                self._setup_router()

                span.set_attribute("initialization_complete", True)
                logger.info(event="task_engine_init_complete")
                task_metrics.increment("operations_total", tags={"operation": "init", "status": "success"})

            except Exception as e:
                logger.error(event="task_engine_init_failed",
                           error=str(e),
                           exc_info=True)
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                task_metrics.increment("operations_total", tags={"operation": "init", "status": "error"})
                raise

    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a chat message with enhanced features and safeguards."""
        with SpanContextManager("process_task_message") as span:
            with task_metrics.time("process_message"):
                try:
                    # Sanitize input
                    sanitized_message = self._sanitize_input(message)
                    span.set_attribute("message_length", len(sanitized_message))

                    logger.info(event="task_processing_start",
                              message_length=len(sanitized_message))

                    # Process message
                    intent_result = await self.classify_intent(sanitized_message)
                    confidence_score = float(intent_result.get("confidence", 0))
                    route_result = await self.determine_route(sanitized_message, context or {})

                    # Handle low confidence
                    if confidence_score < 0.5:
                        logger.warning(event="low_confidence_detected",
                                    confidence=confidence_score,
                                    message=sanitized_message)
                        return self._handle_low_confidence(sanitized_message, intent_result)

                    # Handle routing
                    if route_result["route"] == "human_intervention":
                        logger.info(event="human_intervention_required")
                        return self._trigger_human_intervention(sanitized_message, intent_result)

                    # Generate response
                    response = await self.generate_response(
                        sanitized_message,
                        context or {},
                        intent_result.get("intent", "general_chat")
                    )

                    # Update metrics
                    task_metrics.increment("operations_total", tags={"operation": "process_message", "status": "success"})
                    self._update_metrics(response_time=response.get("processing_time", 0))

                    result = {
                        "response": response.get("text", ""),
                        "intent": intent_result,
                        "confidence": confidence_score,
                        "route": route_result["route"],
                        "requires_human": route_result.get("requires_human", False),
                        "timestamp": datetime.utcnow().isoformat(),
                        "performance_metrics": response.get("metrics", {})
                    }

                    logger.info(event="task_processing_complete",
                              intent=intent_result.get("intent"),
                              confidence=confidence_score,
                              route=route_result["route"])

                    span.set_attribute("processing_success", True)
                    return result

                except Exception as e:
                    logger.error(event="task_processing_failed",
                               error=str(e),
                               exc_info=True)
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR))
                    task_metrics.increment("operations_total", tags={"operation": "process_message", "status": "error"})
                    return self._handle_error(e, sanitized_message)

    def _initialize_chains(self):
        """Initialize the processing chains with enhanced NLP capabilities."""
        # Enhanced chat chain with better context handling
        chat_template = """You are a helpful assistant with access to advanced features.
        Previous conversation context and extracted entities:
        {context}

        User query: {message}

        Based on the context and current query:
        1. Identify key entities and their relationships
        2. Determine user intent with confidence score
        3. Evaluate if external tools or human intervention is needed
        4. Generate a contextually aware response

        Response:"""

        chat_prompt = PromptTemplate(
            input_variables=["context", "message"],
            template=chat_template
        )

        # Initialize memory for context retention
        self.memories["chat"] = ConversationBufferMemory(
            memory_key="context",
            input_key="message",
            output_key="response",
            return_messages=True
        )

        self.chains["chat"] = LLMChain(
            llm=None,  # Will be injected later
            prompt=chat_prompt,
            memory=self.memories["chat"],
            verbose=True
        )

        # Enhanced intent classification with confidence scoring
        intent_template = """Analyze the following message for intent classification:
        Message: {message}

        Provide a detailed analysis including:
        1. Primary intent category
        2. Confidence score (0-1)
        3. Identified entities
        4. Required processing route (internal/external/human)
        5. Priority level (low/medium/high)

        Format the response as a JSON object.
        """

        intent_prompt = PromptTemplate(
            input_variables=["message"],
            template=intent_template
        )

        self.chains["intent"] = LLMChain(
            llm=None,  # Will be injected later
            prompt=intent_prompt,
            verbose=True
        )

    def _setup_router(self):
        """Set up the dynamic query router."""
        router_template = """Given the following user query and context, determine the optimal processing route.
        Query: {message}
        Context: {context}

        Available routes:
        1. internal_processing: For general queries and known patterns
        2. specialized_agent: For complex domain-specific tasks
        3. human_intervention: For sensitive or high-risk requests

        Evaluate:
        1. Query complexity and risk level
        2. Required expertise level
        3. Confidence in automated handling

        Response format: JSON with route and confidence score
        """

        router_prompt = PromptTemplate(
            input_variables=["message", "context"],
            template=router_template
        )

        self.chains["router"] = LLMRouterChain(
            llm=None,  # Will be injected later
            prompt=router_prompt,
            output_parser=RouterOutputParser(),
            verbose=True
        )

    def _sanitize_input(self, message: str) -> str:
        """Sanitize input message for security."""
        # Implement thorough sanitization logic
        return message.strip()

    def _handle_low_confidence(self, message: str, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cases where confidence is below threshold."""
        return {
            "response": "I'm not entirely confident about how to help with that. Would you like to:",
            "options": [
                "Rephrase your question",
                "Speak to a human agent",
                "Try a different approach"
            ],
            "intent": intent_result,
            "confidence": "low",
            "timestamp": datetime.utcnow().isoformat()
        }

    def _trigger_human_intervention(self, message: str, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cases requiring human intervention."""
        return {
            "response": "This request requires human assistance. A support agent will be notified.",
            "intent": intent_result,
            "requires_human": True,
            "priority": "high",
            "timestamp": datetime.utcnow().isoformat()
        }

    def _handle_error(self, error: Exception, message: str) -> Dict[str, Any]:
        """Handle processing errors with fallback mechanisms."""
        logger.error(f"Error processing message: {error}")
        return {
            "response": "I encountered an issue processing your request. Please try again or contact support.",
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _update_metrics(self, response_time: float):
        """Update performance metrics for monitoring."""
        task_metrics.gauge("response_time", response_time)

    async def classify_intent(self, message: str) -> Dict[str, Any]:
        """
        Classify the intent of a message.

        Args:
            message: The input message to classify

        Returns:
            Dict containing the classified intent and confidence
        """
        with SpanContextManager("classify_intent") as span:
            try:
                result = await self.chains["intent"].arun(message=message)
                parsed_result = json.loads(result)
                span.set_attribute("intent", parsed_result.get("intent"))
                span.set_attribute("confidence", parsed_result.get("confidence"))
                task_metrics.increment("operations_total", tags={"operation": "classify_intent", "status": "success"})
                return parsed_result
            except Exception as e:
                logger.error(f"[Chat Task Engine] Error classifying intent: {e}")
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                task_metrics.increment("operations_total", tags={"operation": "classify_intent", "status": "error"})
                raise

    async def generate_response(
        self,
        message: str,
        context: Dict[str, Any],
        intent: str
    ) -> str:
        """
        Generate a response based on the message, context, and intent.

        Args:
            message: The input message
            context: The conversation context
            intent: The classified intent

        Returns:
            str: The generated response
        """
        with SpanContextManager("generate_response") as span:
            try:
                # Format context for the prompt.  Using json.dumps for better handling of complex contexts
                context_str = json.dumps(context, indent=2)

                start_time = datetime.now()
                result = await self.chains["chat"].arun(
                    context=context_str,
                    message=message
                )
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()

                span.set_attribute("response_length", len(result))
                span.set_attribute("processing_time", processing_time)
                task_metrics.increment("operations_total", tags={"operation": "generate_response", "status": "success"})
                return {"text": result.strip(), "processing_time": processing_time}
            except Exception as e:
                logger.error(f"[Chat Task Engine] Error generating response: {e}")
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                task_metrics.increment("operations_total", tags={"operation": "generate_response", "status": "error"})
                raise

    async def determine_route(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the optimal processing route using the router chain."""
        with SpanContextManager("determine_route") as span:
            try:
                # Format context for the prompt. Using json.dumps for better handling of complex contexts
                context_str = json.dumps(context, indent=2)
                route_result = await self.chains["router"].arun(message=message, context=context_str)
                span.set_attribute("route", route_result["route"])
                span.set_attribute("requires_human", route_result.get("requires_human", False))
                task_metrics.increment("operations_total", tags={"operation": "determine_route", "status": "success"})
                return route_result
            except Exception as e:
                logger.error(f"[Chat Task Engine] Error determining route: {e}")
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                task_metrics.increment("operations_total", tags={"operation": "determine_route", "status": "error"})
                return {"route": "internal_processing", "requires_human": False} # Fallback to internal processing
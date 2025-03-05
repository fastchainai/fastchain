"""Chat Agent Manager for handling lifecycle and task delegation."""
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

from src.agents.registry import AgentRegistry
from src.context.context_manager import ContextManager
from .agent import ChatAgent

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatAgentManager:
    """
    Manages the lifecycle of the Chat Agent with basic functionality.
    """

    def __init__(self):
        """Initialize the Chat Agent Manager."""
        try:
            logger.info("Initializing Chat Agent Manager")
            self.agent = None
            self.context_manager = ContextManager()
            self._initialize_agent()

        except Exception as e:
            logger.error(f"Failed to initialize Chat Agent Manager: {str(e)}")
            raise

    def _initialize_agent(self):
        """Initialize and start the Chat Agent."""
        try:
            logger.info("Starting agent initialization")
            self.agent = ChatAgent()

            # Configure prompt template
            prompt_template = self._get_secure_prompt_template()
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "message"]
            )

            # Initialize memory
            memory = ConversationBufferMemory()

            # Initialize LLM chain
            chain = LLMChain(
                llm=self.agent.chat_model.model,
                prompt=prompt,
                verbose=True,
                memory=memory
            )
            self.agent.chat_model.chain = chain

            self.agent.update_status("active")
            self._register_with_registry()
            logger.info("Agent initialization completed")

        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            raise

    async def process_message(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a message with basic functionality."""
        try:
            if not self.agent:
                raise RuntimeError("Chat Agent not initialized")

            # Get or create context
            if session_id:
                context = await self._get_context(session_id)
            else:
                session_id = self._get_secure_session(None)
                context = {}

            # Process message
            result = await self.agent.process_message(message, session_id)

            logger.info(f"Message processed successfully for session {session_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")
            return self._handle_error(e, session_id or "no_session")

    async def _get_context(self, session_id: str) -> Dict[str, Any]:
        """Retrieve context for a session."""
        return self.context_manager.get_context(session_id)

    def _handle_error(self, error: Exception, session_id: str) -> Dict[str, Any]:
        """Handle errors with appropriate responses."""
        logger.error(f"Error handling message: {str(error)}", exc_info=True)
        return {
            "error": str(error),
            "session_id": session_id,
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }

    def _register_with_registry(self):
        """Register with the central registry."""
        if self.agent:
            try:
                registry = AgentRegistry.get_instance()
                agent_name = self.agent.metadata["agent_name"]
                logger.debug(f"Attempting to register agent: {agent_name}")

                # Check if agent is already registered
                if registry.is_agent_registered(agent_name):
                    logger.info(f"Agent '{agent_name}' is already registered, updating metadata")
                    registry.update_agent_metadata(agent_name, self.agent.metadata)
                else:
                    registry.register_agent(agent_name, self.agent.metadata)
                    logger.info(f"Successfully registered agent: {agent_name}")
            except Exception as e:
                logger.warning(f"Non-critical error during agent registration: {str(e)}")
                # Continue execution even if registration fails
                pass

    def start(self):
        """Start the Chat Agent."""
        try:
            if not self.agent:
                self._initialize_agent()
            self.agent.update_status("active")
            logger.info("Chat Agent started successfully")
        except Exception as e:
            logger.error(f"Failed to start agent: {str(e)}")
            raise

    def stop(self):
        """Stop the Chat Agent."""
        if self.agent:
            try:
                self.agent.update_status("inactive")
                logger.info("Chat Agent stopped successfully")
            except Exception as e:
                logger.error(f"Failed to stop agent: {str(e)}")
                raise

    def get_agent_status(self) -> Dict[str, Any]:
        """Get the current status of the Chat Agent."""
        if not self.agent:
            return {"status": "not_initialized"}
        return {
            "status": self.agent.metadata["status"],
            "last_updated": self.agent.metadata["metadata"]["last_updated"]
        }

    def _get_secure_prompt_template(self) -> str:
        """Get a secure prompt template with proper sanitization."""
        return """
        Previous conversation context:
        {context}

        User message:
        {message}

        Assistant:"""

    def _get_secure_session(self, session_id: Optional[str]) -> str:
        """Generate or validate a session ID."""
        if not session_id:
            session_id = str(uuid.uuid4())
            self.context_manager.create_session(session_id)
            logger.info(f"New session created: {session_id}")
        return session_id
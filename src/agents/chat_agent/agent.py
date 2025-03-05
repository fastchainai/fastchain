"""Chat Agent implementation."""
import json
from datetime import datetime
from typing import Dict, Any, Optional

from src.models.chat_model import ChatModel
from src.context.context_manager import ContextManager

class ChatAgent:
    """
    ChatAgent implements a multi-channel chat interface with intent processing
    and task routing capabilities.
    """

    def __init__(self, metadata_file: str = "src/agents/chat_agent/agent.json"):
        """
        Initialize the Chat Agent with configuration from metadata file.

        Args:
            metadata_file: Path to the agent's metadata JSON file
        """
        # Load configuration
        try:
            with open(metadata_file, "r") as f:
                self.metadata = json.load(f)
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            raise

        # Initialize core components
        self.chat_model = ChatModel()
        self.context_manager = ContextManager()

        # Set initial state
        self.metadata["status"] = "initializing"
        self.metadata["metadata"]["last_updated"] = datetime.utcnow().isoformat()

    def update_status(self, status: str) -> None:
        """Update the agent's status and last updated timestamp."""
        self.metadata["status"] = status
        self.metadata["metadata"]["last_updated"] = datetime.utcnow().isoformat()

    async def process_message(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process an incoming chat message.

        Args:
            message: The input message to process
            session_id: Optional session identifier for context management

        Returns:
            Dict containing the processing results
        """
        try:
            # Get or create context for this session
            context = self.context_manager.get_context(session_id) if session_id else {}

            # Process the message using the chat model
            response = self.chat_model.chat(message)

            # Update context with the new interaction
            if session_id:
                context_update = {
                    "last_message": message,
                    "last_response": response,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.context_manager.update_partial_context(session_id, context_update)

            result = {
                "response": response,
                "session_id": session_id,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat()
            }

            return result

        except Exception as e:
            print(f"Error processing message: {str(e)}")
            raise
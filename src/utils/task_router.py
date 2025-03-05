"""Task routing functionality for the Intent Agent."""
from typing import Dict, Any, List
from src.tools import ToolRegistry, Tool, ToolExecutionError
from src.tools.base import ToolContext
from src.utils.logging import Logging

# Initialize logger
logger = Logging(__name__)

class TaskRouter:
    def __init__(self, tool_registry: ToolRegistry = None):
        """Initialize TaskRouter with optional tool registry."""
        if tool_registry is None:
            self.tool_registry = ToolRegistry()
            logger.info("Initializing TaskRouter with new ToolRegistry")
            self._register_default_tools()
        else:
            self.tool_registry = tool_registry
            logger.info("Initializing TaskRouter with provided ToolRegistry")

        # Log available tools
        tools = self.tool_registry.get_all_tools()
        logger.info(f"Available tools for routing: {[t.name for t in tools]}")
        for tool in tools:
            logger.debug(f"Tool {tool.name} metadata: {tool.get_metadata()}")

    def _register_default_tools(self):
        """Register the default set of tools."""
        try:
            # Import SearchTool here to avoid circular dependency
            from src.tools.search import SearchTool
            default_tools = [SearchTool]
            logger.debug(f"Registering default tools: {[t.__name__ for t in default_tools]}")

            for tool_class in default_tools:
                try:
                    self.tool_registry.register(tool_class)
                    logger.info(f"Registered tool {tool_class.__name__}")
                except Exception as e:
                    logger.error(f"Failed to register tool {tool_class.__name__}: {e}")
        except Exception as e:
            logger.error(f"Error loading default tools: {e}")

    def route_task(self, intent: str, entities: Dict[str, List[str]], metadata: Dict[str, Any] = None) -> str:
        """Route a task based on intent and entities using appropriate tools."""
        try:
            # Create standardized context for tool selection
            context_metadata = metadata or {}
            logger.debug("Routing task", intent=intent, entities=entities, metadata=context_metadata)

            # Ensure required fields are present in metadata
            context_metadata.setdefault('intent_confidence', 0.0)
            context_metadata.setdefault('query', '')

            tool_context = ToolContext(
                intent=intent,
                confidence=float(context_metadata.get('intent_confidence', 0.0)),
                entities=entities,
                metadata=context_metadata
            )
            logger.debug("Created tool context", context=tool_context.__dict__)

            # Select appropriate tool
            logger.debug("Selecting tool for intent", intent=intent)
            selected_tool = self.tool_registry.select_tool(
                context={
                    'intent': intent,
                    'entities': entities,
                    'metadata': context_metadata,
                    'confidence': float(context_metadata.get('intent_confidence', 0.0))
                },
                min_confidence=0.1  # Lower threshold for testing
            )

            if not selected_tool:
                logger.warning("No suitable tool found", intent=intent)
                return f"Unable to find appropriate tool for intent: {intent}"

            # Execute the selected tool with proper context
            logger.info("Executing tool", tool_name=selected_tool.name, intent=intent)
            result = selected_tool.execute(
                params={'entities': entities},
                context=tool_context
            )
            logger.debug("Tool execution result", result=result)

            return f"Task routed to {selected_tool.name} (v{selected_tool.version}): {result}"

        except ToolExecutionError as e:
            logger.error("Tool execution failed", error=str(e))
            return f"Error executing task: {str(e)}"
        except Exception as e:
            logger.error("Task routing failed", error=str(e), exc_info=True)
            return f"Error routing task: {str(e)}"
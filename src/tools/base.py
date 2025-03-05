"""Base classes for tool abstraction."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Tuple
from dataclasses import dataclass, field
import logging
import time
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

@dataclass
class ToolMetrics:
    """Metrics for tool execution performance."""
    execution_time: float = 0.0
    success_rate: float = 0.0
    last_execution: Optional[datetime] = None
    total_executions: int = 0
    failed_executions: int = 0

@dataclass
class ToolContext:
    """Standardized context for tool execution."""
    intent: str
    confidence: float
    entities: Dict[str, List[str]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    chain_context: Optional[Dict[str, Any]] = None  # For tool chaining

@dataclass
class ToolResult:
    """Standardized result from tool execution."""
    success: bool
    data: Dict[str, Any]
    next_tools: List[str] = field(default_factory=list)  # For tool chaining
    error_message: Optional[str] = None

class Tool(ABC, Generic[T]):
    """Enhanced abstract base class for all tools."""
    name: str = ""
    description: str = ""
    required_params: List[str] = []
    version: str = "1.0.0"
    compatible_versions: List[str] = []  # For backward compatibility

    def __init__(self):
        if not self.name:
            raise ValueError("Tool must have a name")
        self.metrics = ToolMetrics()
        logger.info(f"Initializing tool: {self.name} (v{self.version})")

    @abstractmethod
    def can_handle(self, context: ToolContext) -> float:
        """Determine if this tool can handle the given context."""
        pass

    def execute(self, params: Dict[str, Any], context: ToolContext) -> ToolResult:
        """Execute the tool with given parameters and track metrics."""
        start_time = time.time()
        self.metrics.total_executions += 1  # Increment counter at start of execution

        try:
            result = self._execute_impl(params, context)
            execution_time = time.time() - start_time

            # Update metrics on success
            self.metrics.execution_time = (self.metrics.execution_time * (self.metrics.total_executions - 1) + execution_time) / self.metrics.total_executions
            self.metrics.last_execution = datetime.now()
            self.metrics.success_rate = (self.metrics.total_executions - self.metrics.failed_executions) / self.metrics.total_executions

            return ToolResult(success=True, data=result)
        except Exception as e:
            # Update metrics on failure
            self.metrics.failed_executions += 1
            self.metrics.success_rate = (self.metrics.total_executions - self.metrics.failed_executions) / max(self.metrics.total_executions, 1)
            logger.error(f"Tool execution failed: {str(e)}")
            return ToolResult(success=False, data={}, error_message=str(e))

    @abstractmethod
    def _execute_impl(self, params: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        """Implementation of tool execution logic."""
        pass

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate that all required parameters are present."""
        if not isinstance(params, dict):
            return False
        return all(param in params for param in self.required_params)

    def get_metadata(self) -> Dict[str, Any]:
        """Get enhanced tool metadata including metrics."""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'compatible_versions': self.compatible_versions,
            'required_params': self.required_params,
            'metrics': {
                'success_rate': self.metrics.success_rate,
                'avg_execution_time': self.metrics.execution_time,
                'total_executions': self.metrics.total_executions,
                'last_execution': self.metrics.last_execution.isoformat() if self.metrics.last_execution else None
            }
        }

class ToolRegistry:
    """Enhanced registry for managing and selecting tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._version_history: Dict[str, List[str]] = {}
        self._chain_definitions: Dict[str, List[Tuple[str, float]]] = {}  # Intent -> [(tool_name, threshold)]
        logger.info("Initializing ToolRegistry")

    def register(self, tool_class: Type[Tool]) -> None:
        """Register a new tool class with version tracking."""
        try:
            tool = tool_class()
            logger.info(f"Registering tool {tool_class.__name__}")

            # Version compatibility check
            if tool.name in self._tools:
                current_version = self._tools[tool.name].version
                if current_version != tool.version:
                    logger.info(f"Updating tool {tool.name} from v{current_version} to v{tool.version}")
                    self._tools[tool.name].compatible_versions.append(current_version)

            self._tools[tool.name] = tool

            # Track version history
            if tool.name not in self._version_history:
                self._version_history[tool.name] = []
            self._version_history[tool.name].append(tool.version)

            logger.info(f"Successfully registered tool: {tool.name} (v{tool.version})")
            logger.debug(f"Current tools: {list(self._tools.keys())}")
        except Exception as e:
            logger.error(f"Failed to register tool {tool_class.__name__}: {e}")
            raise

    def define_chain(self, intent: str, chain: List[Tuple[str, float]]) -> None:
        """Define a tool chain for a specific intent."""
        self._chain_definitions[intent] = chain
        logger.info(f"Defined tool chain for intent '{intent}': {chain}")

    def execute_chain(self, context: Dict[str, Any]) -> List[ToolResult]:
        """Execute a chain of tools for complex tasks."""
        intent = context.get('intent', '')
        if intent not in self._chain_definitions:
            return []

        results = []
        chain_context = {}

        for tool_name, threshold in self._chain_definitions[intent]:
            if tool_name not in self._tools:
                logger.warning(f"Tool {tool_name} not found in registry")
                continue

            tool = self._tools[tool_name]
            tool_context = ToolContext(
                intent=intent,
                confidence=context.get('confidence', 0.0),
                entities=context.get('entities', {}),
                metadata=context.get('metadata', {}),
                chain_context=chain_context
            )

            result = tool.execute(context.get('params', {}), tool_context)
            results.append(result)

            if not result.success or tool.metrics.success_rate < threshold:
                logger.warning(f"Chain execution stopped at {tool_name}: success={result.success}, "
                               f"success_rate={tool.metrics.success_rate}, threshold={threshold}")
                break

            # Update chain context for next tool
            chain_context.update(result.data)

        return results

    def select_tool(self, context: Dict[str, Any], min_confidence: float = 0.1) -> Optional[Tool]:
        """Select the most appropriate tool with enhanced metrics consideration."""
        best_tool = None
        best_confidence = 0.0

        try:
            tool_context = ToolContext(
                intent=context.get('intent', ''),
                confidence=float(context.get('confidence', 0.0)),
                entities=context.get('entities', {}),
                metadata=context.get('metadata', {})
            )

            logger.debug(f"Tool selection started - Intent: {tool_context.intent}")
            logger.debug(f"Context metadata: {tool_context.metadata}")

            # Consider both confidence and historical performance
            for tool in self._tools.values():
                try:
                    confidence = tool.can_handle(tool_context)
                    # Adjust confidence based on historical performance
                    adjusted_confidence = confidence * (0.8 + 0.2 * tool.metrics.success_rate)

                    if adjusted_confidence > best_confidence and adjusted_confidence >= min_confidence:
                        best_tool = tool
                        best_confidence = adjusted_confidence
                except Exception as e:
                    logger.error(f"Error checking tool {tool.name}: {e}")
                    continue

            if best_tool:
                logger.info(f"Selected tool {best_tool.name} with confidence {best_confidence}")
            else:
                logger.warning(f"No suitable tool found for intent '{tool_context.intent}'")

            return best_tool

        except Exception as e:
            logger.error(f"Error in tool selection: {e}", exc_info=True)
            return None

    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tool_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get metadata for all registered tools including metrics."""
        return {name: tool.get_metadata() for name, tool in self._tools.items()}
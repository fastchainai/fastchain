"""Dynamic tool discovery and adaptation system."""
from typing import Dict, Any, List, Optional, Type
from .base import Tool, ToolRegistry
import logging
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

class ToolDiscovery:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.performance_history = self._load_performance_history()
        self.tool_patterns = self._load_tool_patterns()

    def _load_performance_history(self) -> Dict[str, Any]:
        """Load tool performance history."""
        try:
            history_file = "data/tool_performance_history.json"
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    return json.load(f)
            return {"tools": {}, "chains": {}, "last_updated": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Error loading performance history: {e}")
            return {"tools": {}, "chains": {}, "last_updated": datetime.now().isoformat()}

    def _load_tool_patterns(self) -> Dict[str, Any]:
        """Load learned tool patterns."""
        try:
            patterns_file = "data/tool_patterns.json"
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r') as f:
                    return json.load(f)
            return {"patterns": [], "last_updated": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Error loading tool patterns: {e}")
            return {"patterns": [], "last_updated": datetime.now().isoformat()}

    def _save_performance_history(self):
        """Save tool performance history."""
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/tool_performance_history.json", 'w') as f:
                json.dump(self.performance_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving performance history: {e}")

    def _save_tool_patterns(self):
        """Save learned tool patterns."""
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/tool_patterns.json", 'w') as f:
                json.dump(self.tool_patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tool patterns: {e}")

    def record_tool_execution(self, tool_name: str, context: Dict[str, Any], success: bool, execution_time: float):
        """Record tool execution results for learning."""
        try:
            if tool_name not in self.performance_history["tools"]:
                self.performance_history["tools"][tool_name] = {
                    "success_count": 0,
                    "total_executions": 0,
                    "avg_execution_time": 0.0,
                    "intent_patterns": {}
                }

            tool_stats = self.performance_history["tools"][tool_name]
            tool_stats["total_executions"] += 1
            if success:
                tool_stats["success_count"] += 1

            # Update average execution time
            tool_stats["avg_execution_time"] = (
                (tool_stats["avg_execution_time"] * (tool_stats["total_executions"] - 1) + execution_time)
                / tool_stats["total_executions"]
            )

            # Record intent pattern
            intent = context.get("intent", "unknown")
            if intent not in tool_stats["intent_patterns"]:
                tool_stats["intent_patterns"][intent] = {"count": 0, "success_count": 0}
            
            tool_stats["intent_patterns"][intent]["count"] += 1
            if success:
                tool_stats["intent_patterns"][intent]["success_count"] += 1

            self.performance_history["last_updated"] = datetime.now().isoformat()
            self._save_performance_history()
            
            # Learn new patterns if successful
            if success:
                self._learn_tool_pattern(tool_name, context)

        except Exception as e:
            logger.error(f"Error recording tool execution: {e}")

    def _learn_tool_pattern(self, tool_name: str, context: Dict[str, Any]):
        """Learn new tool usage patterns."""
        try:
            new_pattern = {
                "tool_name": tool_name,
                "intent": context.get("intent", "unknown"),
                "entities_present": list(context.get("entities", {}).keys()),
                "metadata_keys": list(context.get("metadata", {}).keys()),
                "learned_at": datetime.now().isoformat()
            }

            # Check if similar pattern exists
            pattern_exists = any(
                p["tool_name"] == tool_name and
                p["intent"] == new_pattern["intent"] and
                set(p["entities_present"]) == set(new_pattern["entities_present"])
                for p in self.tool_patterns["patterns"]
            )

            if not pattern_exists:
                self.tool_patterns["patterns"].append(new_pattern)
                self.tool_patterns["last_updated"] = datetime.now().isoformat()
                self._save_tool_patterns()
                logger.info(f"Learned new tool pattern: {new_pattern}")

        except Exception as e:
            logger.error(f"Error learning tool pattern: {e}")

    def suggest_tool_chain(self, intent: str, context: Dict[str, Any]) -> List[str]:
        """Suggest a tool chain based on learned patterns."""
        try:
            # Find tools that have successfully handled similar intents
            relevant_tools = []
            for tool_name, stats in self.performance_history["tools"].items():
                if intent in stats["intent_patterns"]:
                    pattern_stats = stats["intent_patterns"][intent]
                    if pattern_stats["count"] > 0:
                        success_rate = pattern_stats["success_count"] / pattern_stats["count"]
                        relevant_tools.append((tool_name, success_rate))

            # Sort by success rate
            relevant_tools.sort(key=lambda x: x[1], reverse=True)
            
            # Return chain of most successful tools
            return [tool[0] for tool in relevant_tools[:3]]  # Limit to top 3 tools

        except Exception as e:
            logger.error(f"Error suggesting tool chain: {e}")
            return []

    def get_tool_analytics(self) -> Dict[str, Any]:
        """Get analytics about tool usage and performance."""
        try:
            analytics = {
                "tools": {},
                "patterns": {
                    "total_patterns": len(self.tool_patterns["patterns"]),
                    "last_updated": self.tool_patterns["last_updated"]
                },
                "last_updated": datetime.now().isoformat()
            }

            for tool_name, stats in self.performance_history["tools"].items():
                analytics["tools"][tool_name] = {
                    "success_rate": stats["success_count"] / max(stats["total_executions"], 1),
                    "avg_execution_time": stats["avg_execution_time"],
                    "total_executions": stats["total_executions"],
                    "intent_coverage": len(stats["intent_patterns"])
                }

            return analytics

        except Exception as e:
            logger.error(f"Error getting tool analytics: {e}")
            return {}

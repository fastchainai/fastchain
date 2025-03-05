"""Feedback loop module for continuous learning and adaptation."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
import json
import numpy as np
from collections import defaultdict
from src.utils.logging import Logging

# Initialize logger with the new centralized logging system
logger = Logging(__name__)

class FeedbackLoop:
    def __init__(self):
        """Initialize the feedback loop with storage for metrics and patterns."""
        self.metrics_history = self._load_metrics_history()
        self.adaptation_threshold = 0.7  # Minimum confidence for adaptation
        self.analysis_window = timedelta(days=7)  # Analysis window for trends

    def _load_metrics_history(self) -> Dict[str, Any]:
        """Load historical metrics from storage."""
        try:
            metrics_file = "data/feedback_metrics.json"
            if os.path.exists(metrics_file):
                with open(metrics_file, 'r') as f:
                    return json.load(f)
            return {
                "interactions": [],
                "tool_performance": defaultdict(list),
                "pattern_detection": [],
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Error loading metrics history", error=str(e))
            return {
                "interactions": [],
                "tool_performance": defaultdict(list),
                "pattern_detection": [],
                "last_updated": datetime.now().isoformat()
            }

    def _save_metrics_history(self):
        """Save metrics history to storage."""
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/feedback_metrics.json", 'w') as f:
                json.dump(self.metrics_history, f, indent=2)
        except Exception as e:
            logger.error("Error saving metrics history", error=str(e))

    def process_feedback(self, interaction_data: Dict[str, Any]) -> None:
        """Process new interaction feedback and update metrics."""
        try:
            timestamp = datetime.now().isoformat()

            # Record interaction details
            interaction_record = {
                "timestamp": timestamp,
                "intent": interaction_data.get("intent", {}),
                "success": interaction_data.get("success", False),
                "execution_time": interaction_data.get("execution_time", 0.0),
                "tool_name": interaction_data.get("tool_name", "unknown"),
                "confidence": interaction_data.get("confidence", 0.0)
            }

            self.metrics_history["interactions"].append(interaction_record)

            # Update tool performance metrics
            tool_name = interaction_data.get("tool_name", "unknown")
            self.metrics_history["tool_performance"][tool_name].append({
                "timestamp": timestamp,
                "success": interaction_data.get("success", False),
                "execution_time": interaction_data.get("execution_time", 0.0)
            })

            # Record pattern detection if it's a new pattern
            if interaction_data.get("new_pattern"):
                self.metrics_history["pattern_detection"].append({
                    "timestamp": timestamp,
                    "pattern": interaction_data.get("pattern_description", ""),
                    "intent": interaction_data.get("intent", {}).get("intent", "unknown"),
                    "confidence": interaction_data.get("confidence", 0.0)
                })

            self.metrics_history["last_updated"] = timestamp
            self._save_metrics_history()

            logger.info("Processed feedback for interaction", 
                       intent=interaction_data.get('intent', {}).get('intent', 'unknown'))

        except Exception as e:
            logger.error("Error processing feedback", error=str(e))

    def get_learning_analytics(self) -> Dict[str, Any]:
        """Get analytics about the learning process and adaptations."""
        try:
            now = datetime.now()
            analysis_start = now - self.analysis_window

            # Filter recent interactions
            recent_interactions = [
                i for i in self.metrics_history["interactions"]
                if datetime.fromisoformat(i["timestamp"]) > analysis_start
            ]

            # Calculate success rates and trends
            success_rate = np.mean([i["success"] for i in recent_interactions]) if recent_interactions else 0.0

            # Analyze tool performance
            tool_analytics = {}
            for tool_name, performances in self.metrics_history["tool_performance"].items():
                recent_performances = [
                    p for p in performances
                    if datetime.fromisoformat(p["timestamp"]) > analysis_start
                ]
                if recent_performances:
                    tool_analytics[tool_name] = {
                        "success_rate": np.mean([p["success"] for p in recent_performances]),
                        "avg_execution_time": np.mean([p["execution_time"] for p in recent_performances]),
                        "total_executions": len(recent_performances)
                    }

            # Analyze pattern detection trends
            recent_patterns = [
                p for p in self.metrics_history["pattern_detection"]
                if datetime.fromisoformat(p["timestamp"]) > analysis_start
            ]

            analytics = {
                "overall_metrics": {
                    "success_rate": success_rate,
                    "total_interactions": len(recent_interactions),
                    "unique_intents": len(set(i["intent"].get("intent", "") for i in recent_interactions))
                },
                "tool_performance": tool_analytics,
                "pattern_detection": {
                    "new_patterns_count": len(recent_patterns),
                    "latest_patterns": recent_patterns[-5:] if recent_patterns else []  # Last 5 patterns
                },
                "analysis_period": {
                    "start": analysis_start.isoformat(),
                    "end": now.isoformat()
                }
            }

            return analytics

        except Exception as e:
            logger.error("Error generating learning analytics", error=str(e))
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_adaptation_suggestions(self) -> List[Dict[str, Any]]:
        """Generate suggestions for system adaptation based on metrics."""
        try:
            analytics = self.get_learning_analytics()
            suggestions = []

            # Suggest improvements for underperforming tools
            for tool_name, metrics in analytics["tool_performance"].items():
                if metrics["success_rate"] < self.adaptation_threshold:
                    suggestions.append({
                        "type": "tool_improvement",
                        "tool_name": tool_name,
                        "current_success_rate": metrics["success_rate"],
                        "suggestion": f"Consider reviewing and enhancing {tool_name} implementation "
                                    f"due to low success rate ({metrics['success_rate']:.2%})"
                    })

            # Suggest new tools based on pattern detection
            pattern_clusters = self._analyze_pattern_clusters()
            for cluster in pattern_clusters:
                if cluster["size"] >= 3:  # Threshold for suggesting new tool
                    suggestions.append({
                        "type": "new_tool",
                        "pattern_cluster": cluster["pattern"],
                        "frequency": cluster["size"],
                        "suggestion": f"Consider implementing a new tool for handling "
                                    f"'{cluster['pattern']}' patterns"
                    })

            return suggestions

        except Exception as e:
            logger.error("Error generating adaptation suggestions", error=str(e))
            return []

    def _analyze_pattern_clusters(self) -> List[Dict[str, Any]]:
        """Analyze patterns to identify clusters of similar intents."""
        try:
            recent_patterns = [
                p for p in self.metrics_history["pattern_detection"]
                if datetime.fromisoformat(p["timestamp"]) > (datetime.now() - self.analysis_window)
            ]

            # Simple clustering based on intent similarity
            clusters = defaultdict(int)
            for pattern in recent_patterns:
                clusters[pattern["intent"]] += 1

            return [
                {"pattern": intent, "size": count}
                for intent, count in clusters.items()
            ]

        except Exception as e:
            logger.error("Error analyzing pattern clusters", error=str(e))
            return []
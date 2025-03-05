"""Metrics Module for FastChain AI Framework."""
from .metrics import MetricsCollector
from .config import get_config
from .exporter import Exporter, PrometheusExporter, DatadogExporter
from .store import MetricStore
from .utils import format_metric_name, merge_tags

# Alias MetricsCollector as Metrics for backward compatibility
Metrics = MetricsCollector

class PrometheusMetrics(MetricsCollector):
    """PrometheusMetrics is a convenience wrapper around the MetricsCollector class."""
    def __init__(self, service_name: str, default_tags=None):
        super().__init__(service_name, 
                        exporter=PrometheusExporter(),
                        default_tags=default_tags or {})

__all__ = [
    "MetricsCollector",
    "Metrics",  # Add Metrics alias to __all__
    "PrometheusMetrics",
    "get_config",
    "Exporter",
    "PrometheusExporter", 
    "DatadogExporter",
    "MetricStore",
    "format_metric_name",
    "merge_tags",
]
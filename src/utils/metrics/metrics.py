"""Metrics implementation for recording and exporting various metric types."""
import time
from typing import Dict, Any, Optional, Callable, Union, TypeVar
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry
from .store import MetricStore
from .exporter import Exporter
from .config import get_config
from .utils import merge_tags, format_metric_name

T = TypeVar('T')  # Generic type for the timing function return value

class MetricsCollector:
    """Core metrics implementation for recording counters, gauges, and histograms."""

    def __init__(
        self, 
        service_name: str = "default", 
        exporter: Optional[Exporter] = None, 
        default_tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Initialize the MetricsCollector object.

        Args:
            service_name: Name of the service/agent recording metrics.
            exporter: Optional exporter implementing the Exporter interface.
            default_tags: Dictionary of default tags applied to every metric.
        """
        if not service_name:
            raise ValueError("service_name cannot be empty")

        self.service_name = service_name
        self.config = get_config()
        self.default_tags = default_tags or {}
        self.store = MetricStore()
        self.exporter = exporter

        # Initialize Prometheus registry
        self.registry = CollectorRegistry()
        self.prom_metrics: Dict[str, Union[Counter, Gauge, Histogram]] = {}

    def _get_or_create_prom_metric(self, metric_type: str, name: str, tags: Optional[Dict[str, str]] = None) -> Union[Counter, Gauge, Histogram]:
        """Get or create a Prometheus metric based on type."""
        metric_key = f"{name}_{metric_type}"
        if metric_key not in self.prom_metrics:
            labels = list(self.default_tags.keys())
            if tags:
                labels.extend(list(tags.keys()))

            if metric_type == "counter":
                self.prom_metrics[metric_key] = Counter(name, name, labels, registry=self.registry)
            elif metric_type == "gauge":
                self.prom_metrics[metric_key] = Gauge(name, name, labels, registry=self.registry)
            elif metric_type == "histogram":
                self.prom_metrics[metric_key] = Histogram(name, name, labels, registry=self.registry)

        return self.prom_metrics[metric_key]

    def _record(self, metric_type: str, name: str, value: Union[int, float], labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record a metric with the given type, name, value and optional tags.

        Args:
            metric_type: Type of metric (counter, gauge, histogram)
            name: Metric name 
            value: Numeric value
            labels: Optional dictionary of metric labels
        """
        formatted_name = format_metric_name(name)
        merged_tags = merge_tags(self.default_tags, labels)

        # Record in traditional store
        self.store.record(metric_type, formatted_name, value, merged_tags)

        # Record in Prometheus
        metric = self._get_or_create_prom_metric(metric_type, formatted_name, merged_tags)
        label_values = [str(v) for v in merged_tags.values()]

        if metric_type == "counter":
            metric.labels(*label_values).inc(value)
        elif metric_type == "gauge":
            metric.labels(*label_values).set(value)
        elif metric_type == "histogram":
            metric.labels(*label_values).observe(value)

    def increment(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric.

        Args:
            name: Counter name
            value: Amount to increment by (default: 1)
            labels: Optional metric labels (tags)
        """
        self._record("counter", name, value, labels)

    def gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Update a gauge metric.

        Args:
            name: Gauge name
            value: Current gauge value
            labels: Optional metric labels (tags)
        """
        self._record("gauge", name, value, labels)

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record a histogram value.

        Args:
            name: Histogram name
            value: Value to record
            labels: Optional metric labels (tags)
        """
        self._record("histogram", name, value, labels)

    def time(self, name: str, func: Optional[Callable[[], T]] = None, labels: Optional[Dict[str, str]] = None) -> Union[tuple[T, float], float]:
        """
        Time the execution of a callable or start a timing context.

        Args:
            name: Name of the timing metric
            func: Optional callable to time
            labels: Optional metric labels (tags)

        Returns:
            If func is provided: Tuple of (func result, duration in seconds)
            If func is None: Duration in seconds
        """
        start = time.time()

        if func is None:
            duration = time.time() - start
            self.observe(name, duration, labels)
            return duration

        result = func()
        duration = time.time() - start
        self.observe(name, duration, labels)
        return result, duration

    def export_metrics(self) -> None:
        """Export recorded metrics using the configured exporter."""
        if self.exporter:
            metrics_data = self.store.flush()
            self.exporter.export(metrics_data)

    def get_prometheus_registry(self) -> CollectorRegistry:
        """Get the Prometheus registry containing all metrics."""
        return self.registry
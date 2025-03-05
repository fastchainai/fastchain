import time
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from .config import get_tracing_config

class Tracing:
    """
    The main Tracing class that wraps OpenTelemetry tracer functionalities.
    Provides methods to start and end traces and spans.
    """
    def __init__(self, service_name: str = None):
        config = get_tracing_config()
        self.service_name = service_name if service_name else config["service_name"]
        resource = Resource.create({"service.name": self.service_name})

        # Use always-on sampler if sampling_rate is 1.0, otherwise use a probability sampler.
        sampler = sampling.ALWAYS_ON if config["sampling_rate"] >= 1.0 else sampling.TraceIdRatioBased(config["sampling_rate"])
        self.provider = TracerProvider(resource=resource, sampler=sampler)

        # Setup exporter based on configuration.
        exporter = config["exporter"].lower()
        if exporter == "console":
            span_exporter = ConsoleSpanExporter()
            span_processor = SimpleSpanProcessor(span_exporter)
        elif exporter == "otlp":
            span_exporter = OTLPSpanExporter(endpoint=config["exporter_endpoint"])
            span_processor = BatchSpanProcessor(span_exporter)
        else:
            # Fallback to console exporter if unknown.
            span_exporter = ConsoleSpanExporter()
            span_processor = SimpleSpanProcessor(span_exporter)

        self.provider.add_span_processor(span_processor)
        trace.set_tracer_provider(self.provider)
        self.tracer = trace.get_tracer(self.service_name)

    def start_trace(self, name: str):
        """
        Starts a trace by creating a new span.
        Sets start_time as a span attribute for duration tracking.
        Returns the span which can be ended manually.
        """
        span = self.tracer.start_span(name)
        # Store start time as span attribute
        span.set_attribute("start_time", time.time())
        return span

    def end_trace(self, span):
        """
        Ends the provided span if it is still recording.
        Records duration if start_time was set.
        """
        if span and span.is_recording():
            # Calculate duration if start_time was set
            start_time = span.attributes.get("start_time")
            if start_time is not None:
                duration = time.time() - start_time
                span.set_attribute("duration_seconds", duration)
            span.end()

    def start_span(self, name: str):
        """
        Starts a new span as a context manager.
        Usage:
            with tracer.start_span("span_name") as span:
                # your code
        """
        return self.tracer.start_as_current_span(name)

    def end_span(self, span):
        """
        Ends the provided span if it is still recording.
        """
        if span and span.is_recording():
            span.end()
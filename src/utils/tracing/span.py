from functools import wraps
from opentelemetry import trace

def span_decorator(span_name: str):
    """
    A decorator to automatically create a span around a function call.

    Example:
        @span_decorator("my_span")
        def my_function():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(span_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator

class SpanContextManager:
    """
    A context manager for creating a span.

    Example:
        with SpanContextManager("my_span") as span:
            # your code
    """
    def __init__(self, span_name: str):
        self.span_name = span_name
        self.tracer = trace.get_tracer(__name__)
        self.span = None

    def __enter__(self):
        self.span = self.tracer.start_span(self.span_name)
        if self.span:
            self.span.__enter__()
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span is not None:
            try:
                self.span.__exit__(exc_type, exc_val, exc_tb)
            except Exception as e:
                print(f"Error while ending span: {e}")
            finally:
                self.span = None
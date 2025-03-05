# src/utils/propagator.py

from opentelemetry import propagate

def inject_context(carrier: dict):
    """
    Injects the current trace context into the provided carrier dictionary.
    
    Example:
        carrier = {}
        inject_context(carrier)
    """
    propagate.inject(carrier)

def extract_context(carrier: dict):
    """
    Extracts the trace context from the provided carrier dictionary.
    
    Returns:
        The extracted context.
    """
    return propagate.extract(carrier)

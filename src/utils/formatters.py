"""Formatting utilities for the Intent Agent."""

def format_confidence_color(confidence):
    """Format confidence score with appropriate color."""
    if confidence >= 0.8:
        return "green"
    elif confidence >= 0.5:
        return "orange"
    return "red"

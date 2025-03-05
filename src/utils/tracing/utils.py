def format_trace_id(trace_id: int) -> str:
    """
    Formats a trace id (integer) as a 32-character hexadecimal string.
    
    Example:
        formatted_id = format_trace_id(123456789)
    """
    return format(trace_id, '032x')

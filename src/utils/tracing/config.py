import os

DEFAULT_CONFIG = {
    "service_name": "helix_agent",
    "sampling_rate": 1.0,  # sample all traces
    "exporter": "console",  # default exporter: console
    "exporter_endpoint": "http://localhost:4317",
    "environment": "development"
}

def get_tracing_config():
    """
    Returns the tracing configuration with defaults overridden by environment variables.
    """
    config = DEFAULT_CONFIG.copy()
    config["service_name"] = os.getenv("HELIX_SERVICE_NAME", config["service_name"])
    config["sampling_rate"] = float(os.getenv("HELIX_SAMPLING_RATE", config["sampling_rate"]))
    config["exporter"] = os.getenv("HELIX_EXPORTER", config["exporter"])
    config["exporter_endpoint"] = os.getenv("HELIX_EXPORTER_ENDPOINT", config["exporter_endpoint"])
    config["environment"] = os.getenv("HELIX_ENVIRONMENT", config["environment"])
    return config

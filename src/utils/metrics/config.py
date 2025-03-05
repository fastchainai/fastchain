import os

DEFAULT_CONFIG = {
    "export_interval": 10,  # in seconds
    "sample_rate": 1.0,
    "environment": "development",  # default environment
    "verbose": True,
}

ENV_CONFIGS = {
    "development": {
        "export_interval": 5,
        "verbose": True,
    },
    "testing": {
        "export_interval": 2,
        "verbose": True,
    },
    "staging": {
        "export_interval": 10,
        "verbose": False,
    },
    "production": {
        "export_interval": 15,
        "verbose": False,
    },
}


def get_config():
    env = os.getenv("HELIX_ENV", DEFAULT_CONFIG["environment"])
    config = DEFAULT_CONFIG.copy()
    if env in ENV_CONFIGS:
        config.update(ENV_CONFIGS[env])
    return config

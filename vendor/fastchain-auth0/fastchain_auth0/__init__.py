"""
FastChain Auth0 Integration Package.

This package provides Auth0 authentication capabilities with optional
framework integrations.
"""

from .config import Auth0Config
from .core import Auth0Manager
from .models import TokenPayload, Auth0User
from .exceptions import JWTError, RateLimitExceeded, TokenRefreshError
from .refresh import TokenRefreshManager

__version__ = "0.1.0"
__all__ = [
    "Auth0Manager",
    "Auth0Config",
    "TokenPayload",
    "Auth0User",
    "JWTError",
    "RateLimitExceeded",
    "TokenRefreshError",
    "TokenRefreshManager"
]

# Optional FastAPI integration
try:
    from .integrations.fastapi import FastAPIAuth0Middleware
    __all__.append("FastAPIAuth0Middleware")
except ImportError:
    pass  # FastAPI integration is optional
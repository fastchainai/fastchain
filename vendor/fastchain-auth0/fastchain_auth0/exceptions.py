"""Exceptions for the FastChain Auth0 package."""
from jose.exceptions import JWTError

__all__ = ["JWTError", "RateLimitExceeded", "TokenRefreshError"]

# Re-export JWTError from jose for convenience
# This allows users to import JWTError directly from our package

class RateLimitExceeded(Exception):
    """Raised when token verification rate limit is exceeded."""
    pass

class TokenRefreshError(JWTError):
    """Raised when token refresh operation fails."""
    pass
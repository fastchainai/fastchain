"""Core Auth0 authentication functionality without framework dependencies."""
from typing import Optional, Dict, Any
import asyncio
from jose import jwt
from jose.exceptions import JWTError
import aiohttp
import time

from .config import Auth0Config
from .models import TokenPayload, Auth0User
from .rate_limiting import AsyncTokenRateLimiter
from .exceptions import RateLimitExceeded

class Auth0Manager:
    """Manages Auth0 authentication and token validation."""

    def __init__(self, config: Auth0Config, rate_limit_max: int = 100, rate_limit_window: int = 60):
        """Initialize the Auth0 manager with configuration."""
        self.config = config
        self._jwks_cache: Optional[dict] = None
        self._jwks_timestamp: float = 0
        self._jwks_cache_ttl = 3600  # 1 hour cache TTL
        self._rate_limiter = AsyncTokenRateLimiter(rate_limit_max, rate_limit_window)
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._start_cleanup_task()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._stop_cleanup_task()
        await self.close()

    async def _start_cleanup_task(self):
        """Start background task for cleaning up rate limiting data."""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(60)  # Run cleanup every minute
                await self._rate_limiter.cleanup()

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    async def _stop_cleanup_task(self):
        """Stop the cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper locking."""
        async with self._session_lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=10)
                )
            return self._session

    async def close(self):
        """Close the aiohttp session and cleanup."""
        await self._stop_cleanup_task()
        async with self._session_lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None

    async def get_jwks(self) -> dict:
        """Fetch and cache JWKS from Auth0."""
        now = time.time()
        if self._jwks_cache and (now - self._jwks_timestamp) < self._jwks_cache_ttl:
            return self._jwks_cache

        session = await self._get_session()
        try:
            async with session.get(self.config.get_jwks_url()) as response:
                response.raise_for_status()
                self._jwks_cache = await response.json()
                self._jwks_timestamp = now
                return self._jwks_cache
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise JWTError(f"Failed to fetch JWKS: {str(e)}")

    def _get_rsa_key(self, token_headers: dict, jwks: dict) -> Optional[dict]:
        """Get RSA key matching the token's key ID."""
        for key in jwks.get("keys", []):
            if key["kid"] == token_headers["kid"]:
                return {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        return None

    async def verify_token(self, token: str, enforce_rate_limit: bool = True) -> TokenPayload:
        """
        Verify and decode a JWT token asynchronously.

        Args:
            token: The JWT token to verify
            enforce_rate_limit: Whether to enforce rate limiting

        Returns:
            TokenPayload: The decoded token payload

        Raises:
            JWTError: If token verification fails
            RateLimitExceeded: If rate limit is exceeded
        """
        if enforce_rate_limit:
            is_allowed = await self._rate_limiter.is_allowed(token)
            if not is_allowed:
                remaining, reset_in = await self._rate_limiter.get_remaining(token)
                raise RateLimitExceeded(
                    f"Rate limit exceeded. {remaining} requests remaining, resets in {reset_in} seconds"
                )

        try:
            # Decode header synchronously as it's a local operation
            unverified_header = jwt.get_unverified_header(token)

            # Fetch JWKS asynchronously
            jwks = await self.get_jwks()

            rsa_key = self._get_rsa_key(unverified_header, jwks)
            if not rsa_key:
                raise JWTError("No matching key found")

            # Decode token synchronously as jose doesn't provide async API
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=self.config.algorithms,
                audience=self.config.api_audience,
                issuer=self.config.get_issuer()
            )

            return TokenPayload(**payload)

        except JWTError as e:
            raise JWTError(f"Token verification failed: {str(e)}")
        except Exception as e:
            raise JWTError(f"Unexpected error during token verification: {str(e)}")

    async def get_user_from_token(self, token: str, enforce_rate_limit: bool = True) -> Auth0User:
        """
        Extract user information from a verified token asynchronously.

        Args:
            token: The JWT token
            enforce_rate_limit: Whether to enforce rate limiting

        Returns:
            Auth0User: The authenticated user information
        """
        payload = await self.verify_token(token, enforce_rate_limit)
        return Auth0User(
            sub=payload.sub,
            permissions=payload.permissions or [],
            metadata={
                "iss": payload.iss,
                "aud": payload.aud,
                "scope": payload.scope
            },
            token=token
        )

    def get_token_metadata(self, token: str) -> Dict[str, Any]:
        """
        Get token metadata without verification.
        This operation is not rate limited as it doesn't make external calls.
        """
        try:
            return jwt.get_unverified_claims(token)
        except JWTError as e:
            raise JWTError(f"Failed to decode token: {str(e)}")
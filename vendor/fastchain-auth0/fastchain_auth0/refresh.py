"""Token refresh functionality for Auth0."""
from typing import Optional, Dict
import asyncio
from jose.exceptions import JWTError
import aiohttp

class TokenRefreshManager:
    """Manages token refresh operations."""

    def __init__(
        self,
        domain: str,
        client_id: str,
        client_secret: str,
        default_audience: Optional[str] = None
    ):
        """
        Initialize token refresh manager.

        Args:
            domain: Auth0 domain
            client_id: Auth0 client ID
            client_secret: Auth0 client secret
            default_audience: Default API audience
        """
        self.domain = domain
        self.client_id = client_id
        self.client_secret = client_secret
        self.default_audience = default_audience
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper locking."""
        async with self._session_lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession()
            return self._session

    async def close(self):
        """Close the aiohttp session."""
        async with self._session_lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None

    async def refresh_token(
        self,
        refresh_token: str,
        audience: Optional[str] = None,
        scope: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: The refresh token
            audience: Optional API audience
            scope: Optional scope request

        Returns:
            Dict containing new access_token, refresh_token (if rotated), and token_type

        Raises:
            JWTError: If refresh operation fails
        """
        session = await self._get_session()

        url = f"https://{self.domain}/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token
        }

        if audience or self.default_audience:
            payload["audience"] = audience or self.default_audience

        if scope:
            payload["scope"] = scope

        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_data = await response.json()
                    raise JWTError(
                        f"Token refresh failed: {error_data.get('error_description', 'Unknown error')}"
                    )

                data = await response.json()
                return {
                    "access_token": data["access_token"],
                    "refresh_token": data.get("refresh_token", refresh_token),  # May be rotated
                    "token_type": data["token_type"],
                    "expires_in": data["expires_in"]
                }

        except aiohttp.ClientError as e:
            raise JWTError(f"Failed to refresh token: {str(e)}")
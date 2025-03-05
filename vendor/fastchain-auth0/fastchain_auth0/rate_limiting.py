"""Rate limiting functionality for Auth0 token verification."""
import time
from typing import Dict, Tuple
import asyncio
import math

class AsyncTokenRateLimiter:
    """Async-compatible rate limiter for token verification."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in the time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list[float]] = {}
        self._window_start: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed for the given key."""
        async with self._lock:
            now = time.time()

            # Initialize if key doesn't exist
            if key not in self._requests:
                self._requests[key] = [now]
                self._window_start[key] = now
                return True

            # Check if we need to start a new window
            window_start = self._window_start[key]
            if now - window_start >= self.window_seconds:
                self._requests[key] = [now]
                self._window_start[key] = now
                return True

            # Check if under limit
            if len(self._requests[key]) >= self.max_requests:
                return False

            # Add current timestamp and allow request
            self._requests[key].append(now)
            return True

    async def get_remaining(self, key: str) -> Tuple[int, int]:
        """Get remaining requests and reset time for the key.

        Returns:
            Tuple of (remaining_requests, seconds_until_reset)
        """
        async with self._lock:
            now = time.time()
            if key not in self._requests:
                return self.max_requests, 0

            window_start = self._window_start[key]
            elapsed = now - window_start

            # If window has expired, return full quota
            if elapsed >= self.window_seconds:
                return self.max_requests, 0

            # Calculate remaining requests and reset time
            current_requests = len(self._requests[key])
            remaining = max(0, self.max_requests - current_requests)
            # Use ceiling function and add small buffer to ensure positive value
            reset_in = math.ceil(self.window_seconds - elapsed) + 1

            return remaining, reset_in

    async def cleanup(self):
        """Clean up expired entries."""
        async with self._lock:
            now = time.time()
            expired_keys = [
                key for key, start in self._window_start.items()
                if now - start >= self.window_seconds
            ]
            for key in expired_keys:
                del self._requests[key]
                del self._window_start[key]
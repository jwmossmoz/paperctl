"""Rate limiter for respecting API limits."""

import asyncio
import time
from collections import deque


class RateLimiter:
    """Token bucket rate limiter for API requests.

    Papertrail allows 25 requests per 5 seconds.
    """

    def __init__(self, max_requests: int = 25, window_seconds: float = 5.0) -> None:
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a request slot is available."""
        async with self._lock:
            now = time.time()

            # Remove requests outside the window
            while self.requests and self.requests[0] <= now - self.window_seconds:
                self.requests.popleft()

            # If at limit, wait until oldest request expires
            if len(self.requests) >= self.max_requests:
                sleep_time = self.requests[0] + self.window_seconds - now
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    # Remove expired requests after sleeping
                    now = time.time()
                    while self.requests and self.requests[0] <= now - self.window_seconds:
                        self.requests.popleft()

            # Record this request
            self.requests.append(time.time())

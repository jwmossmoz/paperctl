"""Retry utilities for rate limiting."""

import time
from collections.abc import Callable
from typing import TypeVar

from paperctl.client.exceptions import RateLimitError

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> T:
    """Retry a function with exponential backoff on rate limit errors.

    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Result of function call

    Raises:
        RateLimitError: If max retries exceeded
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        except RateLimitError as e:
            if attempt == max_retries:
                raise

            # Use retry_after from error if available, otherwise exponential backoff
            if e.retry_after:
                delay = min(float(e.retry_after), max_delay)
            else:
                delay = min(base_delay * (2**attempt), max_delay)

            time.sleep(delay)

    # Should never reach here, but satisfy type checker
    raise RateLimitError()

"""Retry utilities for rate limiting."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

from paperctl.client.exceptions import RateLimitError

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_on: tuple[type[Exception], ...] = (RateLimitError,),
    retry_if: Callable[[Exception], bool] | None = None,
) -> T:
    """Retry a function with exponential backoff on rate limit errors.

    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        retry_on: Exception types to retry on
        retry_if: Optional predicate to decide retry for other exceptions

    Returns:
        Result of function call

    Raises:
        RateLimitError: If max retries exceeded
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            should_retry = isinstance(e, retry_on)
            if retry_if is not None:
                should_retry = should_retry or retry_if(e)
            if not should_retry:
                raise

            if attempt == max_retries:
                raise

            # Use retry_after from error if available, otherwise exponential backoff
            if isinstance(e, RateLimitError) and e.retry_after:
                delay = min(float(e.retry_after), max_delay)
            else:
                delay = min(base_delay * (2**attempt), max_delay)

            time.sleep(delay)

    # Should never reach here, but satisfy type checker
    raise RateLimitError()


async def async_retry_with_backoff(
    func: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_on: tuple[type[Exception], ...] = (RateLimitError,),
    retry_if: Callable[[Exception], bool] | None = None,
) -> T:
    """Retry an async function with exponential backoff on rate limit errors.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        retry_on: Exception types to retry on
        retry_if: Optional predicate to decide retry for other exceptions

    Returns:
        Result of function call

    Raises:
        RateLimitError: If max retries exceeded
    """
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            should_retry = isinstance(e, retry_on)
            if retry_if is not None:
                should_retry = should_retry or retry_if(e)
            if not should_retry:
                raise

            if attempt == max_retries:
                raise

            if isinstance(e, RateLimitError) and e.retry_after:
                delay = min(float(e.retry_after), max_delay)
            else:
                delay = min(base_delay * (2**attempt), max_delay)

            await asyncio.sleep(delay)

    raise RateLimitError()

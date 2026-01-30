"""Async Papertrail API client for parallel requests."""

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

import httpx

from paperctl.client.exceptions import APIError, AuthenticationError, RateLimitError
from paperctl.client.models import Event, SearchResponse, System
from paperctl.utils.rate_limiter import AsyncRateLimiter
from paperctl.utils.retry import async_retry_with_backoff


def _should_retry_error(error: Exception) -> bool:
    if isinstance(error, APIError):
        return error.status_code == 0 or error.status_code >= 500
    return False


class AsyncPapertrailClient:
    """Async client for Papertrail API."""

    BASE_URL = "https://papertrailapp.com/api/v1"

    def __init__(
        self,
        api_token: str,
        timeout: float = 30.0,
        rate_limiter: AsyncRateLimiter | None = None,
    ) -> None:
        """Initialize async client.

        Args:
            api_token: Papertrail API token
            timeout: Request timeout in seconds
            rate_limiter: Optional rate limiter for API requests
        """
        self.api_token = api_token
        self.timeout = timeout
        self._rate_limiter = rate_limiter or AsyncRateLimiter()
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "X-Papertrail-Token": api_token,
                "Accept": "application/json",
            },
            timeout=timeout,
        )

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make async API request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit exceeded
            APIError: If API returns an error
        """
        try:
            await self._rate_limiter.acquire()
            response = await self._client.request(method=method, url=endpoint, params=params)

            if response.status_code == 401:
                raise AuthenticationError("Invalid API token")

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError(retry_after=int(retry_after) if retry_after else None)

            if response.status_code >= 400:
                try:
                    error_msg = response.json().get("message", response.text)
                except Exception:
                    error_msg = response.text
                raise APIError(response.status_code, error_msg)

            result: dict[str, Any] = response.json()
            return result

        except httpx.HTTPError as e:
            raise APIError(0, f"HTTP error: {e}") from e

    async def search(
        self,
        query: str | None = None,
        system_id: int | None = None,
        min_time: datetime | None = None,
        max_time: datetime | None = None,
        limit: int = 1000,
        max_id: str | None = None,
    ) -> SearchResponse:
        """Search for log events.

        Args:
            query: Search query
            system_id: Filter by system ID
            min_time: Start time (UTC)
            max_time: End time (UTC)
            limit: Maximum events per request
            max_id: Maximum event ID for pagination

        Returns:
            Search response with events
        """
        params: dict[str, Any] = {"limit": limit}

        if query:
            params["q"] = query
        if system_id:
            params["system_id"] = system_id
        if min_time:
            params["min_time"] = int(min_time.timestamp())
        if max_time:
            params["max_time"] = int(max_time.timestamp())
        if max_id:
            params["max_id"] = max_id

        data = await async_retry_with_backoff(
            lambda: self._request("GET", "/events/search.json", params=params),
            retry_if=_should_retry_error,
        )
        return SearchResponse.model_validate(data)

    async def search_iter(
        self,
        query: str | None = None,
        system_id: int | None = None,
        min_time: datetime | None = None,
        max_time: datetime | None = None,
        total_limit: int | None = None,
        page_limit: int = 1000,
    ) -> AsyncIterator[Event]:
        """Iterate through search results with automatic pagination.

        Args:
            query: Search query
            system_id: Filter by system ID
            min_time: Start time (UTC)
            max_time: End time (UTC)
            total_limit: Maximum events to return (None for no limit)
            page_limit: Maximum events per request

        Yields:
            Individual log events
        """
        max_id = None
        total_events = 0

        while True:
            if total_limit is not None and total_limit <= total_events:
                break

            request_limit = page_limit
            if total_limit is not None:
                request_limit = min(page_limit, max(total_limit - total_events, 0))

            response = await self.search(
                query=query,
                system_id=system_id,
                min_time=min_time,
                max_time=max_time,
                limit=request_limit,
                max_id=max_id,
            )

            if not response.events:
                break

            for event in response.events:
                yield event
                total_events += 1
                if total_limit is not None and total_events >= total_limit:
                    return

            if response.reached_beginning or response.reached_time_limit:
                break

            max_id = response.min_id

    async def list_systems(self) -> list[System]:
        """List all systems.

        Returns:
            List of systems
        """
        data = await async_retry_with_backoff(
            lambda: self._request("GET", "/systems.json"),
            retry_if=_should_retry_error,
        )
        return [System.model_validate(s) for s in data]

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncPapertrailClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

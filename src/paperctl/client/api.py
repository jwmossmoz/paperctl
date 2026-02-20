"""SolarWinds Observability API client implementation."""

from collections.abc import Iterator
from datetime import datetime
from typing import Any

import httpx

from paperctl.client.exceptions import APIError, AuthenticationError, RateLimitError
from paperctl.client.models import EntitiesResponse, Entity, Event, LogsResponse
from paperctl.utils.rate_limiter import RateLimiter
from paperctl.utils.retry import retry_with_backoff

DEFAULT_API_URL = "https://api.na-01.cloud.solarwinds.com"


def _should_retry_error(error: Exception) -> bool:
    if isinstance(error, APIError):
        return error.status_code == 0 or error.status_code >= 500
    return False


class SWOClient:
    """Client for interacting with SolarWinds Observability API."""

    def __init__(
        self,
        api_token: str,
        api_url: str = DEFAULT_API_URL,
        timeout: float = 30.0,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        """Initialize SWO client.

        Args:
            api_token: SolarWinds Observability API token
            api_url: Base URL for the API
            timeout: Request timeout in seconds
            rate_limiter: Optional rate limiter for API requests
        """
        self.api_token = api_token
        self.api_url = api_url
        self.timeout = timeout
        self._rate_limiter = rate_limiter or RateLimiter()
        self._client = httpx.Client(
            base_url=api_url,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json",
            },
            timeout=timeout,
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        url: str | None = None,
    ) -> dict[str, Any]:
        """Make an API request with error handling.

        Args:
            method: HTTP method
            endpoint: API endpoint (ignored if url is provided)
            params: Query parameters
            url: Full URL to request (for pagination)

        Returns:
            Response JSON

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit exceeded
            APIError: If API returns an error
        """
        try:
            self._rate_limiter.acquire()

            if url:
                response = self._client.request(method=method, url=url)
            else:
                response = self._client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                )

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

    def get_logs(
        self,
        filter_query: str | None = None,
        hostname: str | None = None,
        group: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page_size: int = 1000,
        direction: str = "backward",
        page_url: str | None = None,
    ) -> LogsResponse:
        """Fetch logs from the API.

        Args:
            filter_query: Filter query string
            hostname: Filter by hostname (prepended as host:"value")
            group: Filter by group name
            start_time: Start time (UTC)
            end_time: End time (UTC)
            page_size: Maximum events per page
            direction: Sort direction (backward or forward)
            page_url: Full URL for pagination (overrides other params)

        Returns:
            Logs response with events and page info
        """
        if page_url:
            data = self._request("GET", "", url=page_url)
            return LogsResponse.model_validate(data)

        params: dict[str, Any] = {
            "pageSize": page_size,
            "direction": direction,
        }

        # Build filter string
        filter_parts: list[str] = []
        if hostname:
            filter_parts.append(f'host:"{hostname}"')
        if group:
            filter_parts.append(f'group:"{group}"')
        if filter_query:
            filter_parts.append(filter_query)

        if filter_parts:
            params["filter"] = " ".join(filter_parts)

        if start_time:
            params["startTime"] = start_time.isoformat()
        if end_time:
            params["endTime"] = end_time.isoformat()

        data = self._request("GET", "/v1/logs", params=params)
        return LogsResponse.model_validate(data)

    def logs_iter(
        self,
        filter_query: str | None = None,
        hostname: str | None = None,
        group: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        total_limit: int | None = None,
        page_size: int = 1000,
    ) -> Iterator[Event]:
        """Iterate through logs with automatic pagination.

        Args:
            filter_query: Filter query string
            hostname: Filter by hostname
            group: Filter by group name
            start_time: Start time (UTC)
            end_time: End time (UTC)
            total_limit: Maximum events to return (None for no limit)
            page_size: Maximum events per page

        Yields:
            Individual log events
        """
        next_page: str | None = None
        total_events = 0

        while True:
            if total_limit is not None and total_limit <= total_events:
                break

            request_size = page_size
            if total_limit is not None:
                request_size = min(page_size, max(total_limit - total_events, 0))

            def do_fetch(
                request_size: int = request_size,
                next_page: str | None = next_page,
            ) -> LogsResponse:
                return self.get_logs(
                    filter_query=filter_query,
                    hostname=hostname,
                    group=group,
                    start_time=start_time,
                    end_time=end_time,
                    page_size=request_size,
                    page_url=next_page,
                )

            response = retry_with_backoff(
                do_fetch,
                retry_if=_should_retry_error,
            )

            if not response.logs:
                break

            for event in response.logs:
                yield event
                total_events += 1
                if total_limit is not None and total_events >= total_limit:
                    return

            if not response.page_info.next_page:
                break

            next_page = response.page_info.next_page

    def list_entities(
        self,
        entity_type: str = "Host",
        name: str | None = None,
        page_size: int = 100,
    ) -> list[Entity]:
        """List entities, auto-paginating through all pages.

        Args:
            entity_type: Entity type filter (e.g., "Host")
            name: Optional name filter
            page_size: Page size for each request

        Returns:
            List of all entities
        """
        params: dict[str, Any] = {
            "type": entity_type,
            "pageSize": page_size,
        }
        if name:
            params["name"] = name

        all_entities: list[Entity] = []
        next_page: str | None = None

        while True:
            if next_page:
                data = self._request("GET", "", url=next_page)
            else:
                data = self._request("GET", "/v1/entities", params=params)

            resp = EntitiesResponse.model_validate(data)
            all_entities.extend(resp.entities)

            if not resp.page_info.next_page:
                break
            next_page = resp.page_info.next_page

        return all_entities

    def get_entity(self, entity_id: str) -> Entity:
        """Get entity details.

        Args:
            entity_id: Entity ID

        Returns:
            Entity details
        """
        data = self._request("GET", f"/v1/entities/{entity_id}")
        return Entity.model_validate(data)

    def list_entity_types(self) -> list[str]:
        """List available entity types.

        Returns:
            List of entity type strings
        """
        data = self._request("GET", "/v1/metadata/entities/types")
        types: list[str] = data.get("types", data) if isinstance(data, dict) else data
        return types

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "SWOClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

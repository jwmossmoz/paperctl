"""Papertrail API client implementation."""

from collections.abc import Iterator
from datetime import datetime
from typing import Any

import httpx

from paperctl.client.exceptions import APIError, AuthenticationError, RateLimitError
from paperctl.client.models import Archive, Event, Group, SearchResponse, System


class PapertrailClient:
    """Client for interacting with Papertrail API."""

    BASE_URL = "https://papertrailapp.com/api/v1"

    def __init__(self, api_token: str, timeout: float = 30.0) -> None:
        """Initialize Papertrail client.

        Args:
            api_token: Papertrail API token
            timeout: Request timeout in seconds
        """
        self.api_token = api_token
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "X-Papertrail-Token": api_token,
                "Accept": "application/json",
            },
            timeout=timeout,
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request with error handling.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON body

        Returns:
            Response JSON

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit exceeded
            APIError: If API returns an error
        """
        try:
            response = self._client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data,
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

            return response.json()

        except httpx.HTTPError as e:
            raise APIError(0, f"HTTP error: {e}") from e

    def search(
        self,
        query: str | None = None,
        system_id: int | None = None,
        group_id: int | None = None,
        min_time: datetime | None = None,
        max_time: datetime | None = None,
        limit: int = 1000,
        min_id: str | None = None,
        max_id: str | None = None,
    ) -> SearchResponse:
        """Search for log events.

        Args:
            query: Search query
            system_id: Filter by system ID
            group_id: Filter by group ID
            min_time: Start time (UTC)
            max_time: End time (UTC)
            limit: Maximum events per request
            min_id: Minimum event ID for pagination
            max_id: Maximum event ID for pagination

        Returns:
            Search response with events
        """
        params: dict[str, Any] = {"limit": limit}

        if query:
            params["q"] = query
        if system_id:
            params["system_id"] = system_id
        if group_id:
            params["group_id"] = group_id
        if min_time:
            params["min_time"] = int(min_time.timestamp())
        if max_time:
            params["max_time"] = int(max_time.timestamp())
        if min_id:
            params["min_id"] = min_id
        if max_id:
            params["max_id"] = max_id

        data = self._request("GET", "/events/search.json", params=params)
        return SearchResponse.model_validate(data)

    def search_iter(
        self,
        query: str | None = None,
        system_id: int | None = None,
        group_id: int | None = None,
        min_time: datetime | None = None,
        max_time: datetime | None = None,
        limit: int = 1000,
    ) -> Iterator[Event]:
        """Iterate through search results with automatic pagination.

        Args:
            query: Search query
            system_id: Filter by system ID
            group_id: Filter by group ID
            min_time: Start time (UTC)
            max_time: End time (UTC)
            limit: Maximum events per request

        Yields:
            Individual log events
        """
        max_id = None
        total_events = 0

        while True:
            response = self.search(
                query=query,
                system_id=system_id,
                group_id=group_id,
                min_time=min_time,
                max_time=max_time,
                limit=limit,
                max_id=max_id,
            )

            if not response.events:
                break

            for event in response.events:
                yield event
                total_events += 1

            if response.reached_beginning or response.reached_time_limit:
                break

            max_id = response.min_id

    def list_systems(self) -> list[System]:
        """List all systems.

        Returns:
            List of systems
        """
        data = self._request("GET", "/systems.json")
        return [System.model_validate(s) for s in data]

    def get_system(self, system_id: int) -> System:
        """Get system details.

        Args:
            system_id: System ID

        Returns:
            System details
        """
        data = self._request("GET", f"/systems/{system_id}.json")
        return System.model_validate(data)

    def list_groups(self) -> list[Group]:
        """List all groups.

        Returns:
            List of groups
        """
        data = self._request("GET", "/groups.json")
        return [Group.model_validate(g) for g in data]

    def get_group(self, group_id: int) -> Group:
        """Get group details.

        Args:
            group_id: Group ID

        Returns:
            Group details with systems
        """
        data = self._request("GET", f"/groups/{group_id}.json")
        return Group.model_validate(data)

    def list_archives(self) -> list[Archive]:
        """List available archives.

        Returns:
            List of archives
        """
        data = self._request("GET", "/archives.json")
        return [Archive.model_validate(a) for a in data]

    def download_archive(self, filename: str) -> bytes:
        """Download an archive file.

        Args:
            filename: Archive filename

        Returns:
            Archive file content
        """
        response = self._client.get(f"/archives/{filename}/download")
        response.raise_for_status()
        return response.content

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "PapertrailClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

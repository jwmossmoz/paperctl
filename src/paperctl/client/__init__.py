"""SolarWinds Observability API client."""

from paperctl.client.api import SWOClient
from paperctl.client.exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    SWOError,
)
from paperctl.client.models import EntitiesResponse, Entity, Event, LogsResponse, PageInfo

__all__ = [
    "SWOClient",
    "SWOError",
    "AuthenticationError",
    "RateLimitError",
    "APIError",
    "Event",
    "LogsResponse",
    "PageInfo",
    "Entity",
    "EntitiesResponse",
]

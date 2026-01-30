"""Papertrail API client."""

from paperctl.client.api import PapertrailClient
from paperctl.client.exceptions import (
    APIError,
    AuthenticationError,
    PapertrailError,
    RateLimitError,
)
from paperctl.client.models import Archive, Event, Group, SearchResponse, System

__all__ = [
    "PapertrailClient",
    "PapertrailError",
    "AuthenticationError",
    "RateLimitError",
    "APIError",
    "Event",
    "SearchResponse",
    "System",
    "Group",
    "Archive",
]

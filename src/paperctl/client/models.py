"""Pydantic models for Papertrail API responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class Event(BaseModel):
    """A log event from Papertrail."""

    id: str
    source_id: int
    source_name: str
    source_ip: str | None = None
    facility: str | int | None = None
    severity: str | int | None = None
    program: str
    message: str
    received_at: datetime
    generated_at: datetime | None = None
    display_received_at: str


class SearchResponse(BaseModel):
    """Response from search API."""

    events: list[Event]
    min_id: str | None = None
    max_id: str | None = None
    reached_beginning: bool = False
    reached_end: bool = False
    reached_time_limit: bool = False


class System(BaseModel):
    """A system in Papertrail."""

    id: int
    name: str
    last_event_at: datetime | None = None
    auto_delete: bool | None = None
    ip_address: str | None = None
    hostname: str | None = None
    syslog_hostname: str | None = None


class Group(BaseModel):
    """A group in Papertrail."""

    id: int
    name: str
    system_wildcard: str | None = None
    systems: list[System] = Field(default_factory=list)


class Archive(BaseModel):
    """An archive file in Papertrail."""

    filename: str
    start: datetime
    end: datetime
    filesize: int
    formatted_filesize: str

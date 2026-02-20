"""Pydantic models for SolarWinds Observability API responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class Event(BaseModel):
    """A log event from SolarWinds Observability."""

    time: datetime
    message: str
    hostname: str = ""
    severity: str | None = None
    program: str | None = None


class PageInfo(BaseModel):
    """Pagination info from SolarWinds Observability API."""

    prev_page: str = Field(default="", alias="prevPage")
    next_page: str = Field(default="", alias="nextPage")

    model_config = {"populate_by_name": True}


class LogsResponse(BaseModel):
    """Response from the logs API."""

    logs: list[Event] = Field(default_factory=list)
    page_info: PageInfo = Field(default_factory=PageInfo, alias="pageInfo")

    model_config = {"populate_by_name": True}


class Entity(BaseModel):
    """An entity in SolarWinds Observability."""

    id: str
    type: str
    name: str
    display_name: str = Field(default="", alias="displayName")
    created_time: datetime | None = Field(default=None, alias="createdTime")
    updated_time: datetime | None = Field(default=None, alias="updatedTime")
    last_seen_time: datetime | None = Field(default=None, alias="lastSeenTime")
    in_maintenance: bool = Field(default=False, alias="inMaintenance")
    tags: dict[str, str] = Field(default_factory=dict)
    attributes: dict[str, str] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class EntitiesResponse(BaseModel):
    """Response from the entities API."""

    entities: list[Entity] = Field(default_factory=list)
    page_info: PageInfo = Field(default_factory=PageInfo, alias="pageInfo")

    model_config = {"populate_by_name": True}

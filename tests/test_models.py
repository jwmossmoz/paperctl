"""Tests for Pydantic models."""

from datetime import UTC, datetime

from paperctl.client.models import EntitiesResponse, Entity, Event, LogsResponse, PageInfo


def test_event_parsing() -> None:
    """Test Event parses from SWO JSON."""
    data = {
        "time": "2024-01-01T00:00:00Z",
        "message": "test log message",
        "hostname": "web-1",
        "severity": "info",
        "program": "nginx",
    }
    event = Event.model_validate(data)
    assert event.message == "test log message"
    assert event.hostname == "web-1"
    assert event.severity == "info"
    assert event.program == "nginx"
    assert event.time.year == 2024


def test_event_optional_fields() -> None:
    """Test Event with minimal fields."""
    data = {
        "time": "2024-06-15T12:30:00Z",
        "message": "minimal event",
    }
    event = Event.model_validate(data)
    assert event.message == "minimal event"
    assert event.hostname == ""
    assert event.severity is None
    assert event.program is None


def test_page_info_aliases() -> None:
    """Test PageInfo parses camelCase aliases."""
    data = {
        "prevPage": "https://api.example.com/v1/logs?cursor=abc",
        "nextPage": "https://api.example.com/v1/logs?cursor=def",
    }
    page_info = PageInfo.model_validate(data)
    assert page_info.prev_page == "https://api.example.com/v1/logs?cursor=abc"
    assert page_info.next_page == "https://api.example.com/v1/logs?cursor=def"


def test_page_info_empty() -> None:
    """Test PageInfo defaults to empty strings."""
    page_info = PageInfo.model_validate({})
    assert page_info.prev_page == ""
    assert page_info.next_page == ""


def test_logs_response() -> None:
    """Test LogsResponse with pageInfo alias."""
    data = {
        "logs": [
            {
                "time": "2024-01-01T00:00:00Z",
                "message": "event 1",
                "hostname": "web-1",
            }
        ],
        "pageInfo": {
            "prevPage": "",
            "nextPage": "https://api.example.com/next",
        },
    }
    response = LogsResponse.model_validate(data)
    assert len(response.logs) == 1
    assert response.logs[0].message == "event 1"
    assert response.page_info.next_page == "https://api.example.com/next"


def test_entity_with_aliases() -> None:
    """Test Entity parses camelCase aliases."""
    data = {
        "id": "e-123",
        "type": "Host",
        "name": "web-1.example.com",
        "displayName": "Web Server 1",
        "createdTime": "2024-01-01T00:00:00Z",
        "updatedTime": "2024-06-01T00:00:00Z",
        "lastSeenTime": "2024-06-15T12:00:00Z",
        "inMaintenance": True,
        "tags": {"env": "production"},
        "attributes": {"os": "linux"},
    }
    entity = Entity.model_validate(data)
    assert entity.id == "e-123"
    assert entity.display_name == "Web Server 1"
    assert entity.last_seen_time is not None
    assert entity.last_seen_time.year == 2024
    assert entity.in_maintenance is True
    assert entity.tags == {"env": "production"}
    assert entity.attributes == {"os": "linux"}


def test_entity_optional_fields() -> None:
    """Test Entity with minimal required fields."""
    data = {
        "id": "e-456",
        "type": "Service",
        "name": "api-gateway",
    }
    entity = Entity.model_validate(data)
    assert entity.display_name == ""
    assert entity.created_time is None
    assert entity.last_seen_time is None
    assert entity.in_maintenance is False
    assert entity.tags == {}


def test_entities_response() -> None:
    """Test EntitiesResponse parsing."""
    data = {
        "entities": [
            {"id": "e-1", "type": "Host", "name": "web-1"},
            {"id": "e-2", "type": "Host", "name": "web-2"},
        ],
        "pageInfo": {"prevPage": "", "nextPage": ""},
    }
    response = EntitiesResponse.model_validate(data)
    assert len(response.entities) == 2
    assert response.entities[0].name == "web-1"
    assert response.page_info.next_page == ""


def test_entity_serialization_uses_snake_case() -> None:
    """Test Entity model_dump uses snake_case field names."""
    entity = Entity(
        id="e-1",
        type="Host",
        name="web-1",
        display_name="Web 1",
        in_maintenance=False,
        last_seen_time=datetime(2024, 1, 1, tzinfo=UTC),
    )
    dumped = entity.model_dump()
    assert "display_name" in dumped
    assert "in_maintenance" in dumped
    assert "last_seen_time" in dumped

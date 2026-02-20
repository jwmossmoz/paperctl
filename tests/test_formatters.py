"""Tests for formatters."""

from datetime import UTC, datetime

from paperctl.client.models import Entity, Event
from paperctl.formatters import CSVFormatter, JSONFormatter, TextFormatter


def test_text_formatter_event() -> None:
    """Test text formatter for events."""
    event = Event(
        time=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        message="Test message",
        hostname="test-host",
        severity="info",
        program="test",
    )

    formatter = TextFormatter()
    result = formatter.format_event(event)

    assert "test-host" in result
    assert "test" in result
    assert "Test message" in result


def test_json_formatter_events() -> None:
    """Test JSON formatter for events."""
    event = Event(
        time=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        message="Test message",
        hostname="test-host",
        severity="info",
        program="test",
    )

    formatter = JSONFormatter()
    result = formatter.format_events([event])

    assert isinstance(result, str)
    assert "test-host" in result
    assert "Test message" in result


def test_csv_formatter_entities() -> None:
    """Test CSV formatter for entities."""
    entity = Entity(
        id="e-123",
        type="Host",
        name="test-system",
        display_name="Test System",
    )

    formatter = CSVFormatter()
    result = formatter.format_entities([entity])

    assert "test-system" in result
    assert "e-123" in result
    assert "id,type,name" in result

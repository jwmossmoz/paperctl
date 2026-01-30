"""Tests for formatters."""

from datetime import UTC, datetime

from paperctl.client.models import Event, System
from paperctl.formatters import CSVFormatter, JSONFormatter, TextFormatter


def test_text_formatter_event() -> None:
    """Test text formatter for events."""
    event = Event(
        id="123",
        source_id=1,
        source_name="test-host",
        source_ip="1.2.3.4",
        facility="user",
        severity="info",
        program="test",
        message="Test message",
        received_at=datetime.now(UTC),
        display_received_at="2024-01-01 00:00:00",
    )

    formatter = TextFormatter()
    result = formatter.format_event(event)

    assert "test-host" in result
    assert "test" in result
    assert "Test message" in result


def test_json_formatter_events() -> None:
    """Test JSON formatter for events."""
    event = Event(
        id="123",
        source_id=1,
        source_name="test-host",
        source_ip="1.2.3.4",
        facility="user",
        severity="info",
        program="test",
        message="Test message",
        received_at=datetime.now(UTC),
        display_received_at="2024-01-01 00:00:00",
    )

    formatter = JSONFormatter()
    result = formatter.format_events([event])

    assert isinstance(result, str)
    assert "test-host" in result
    assert "Test message" in result


def test_csv_formatter_systems() -> None:
    """Test CSV formatter for systems."""
    system = System(
        id=1,
        name="test-system",
        ip_address="1.2.3.4",
        hostname="test",
    )

    formatter = CSVFormatter()
    result = formatter.format_systems([system])

    assert "test-system" in result
    assert "1.2.3.4" in result
    assert "id,name,ip_address" in result

"""Tests for time parsing utilities."""

from datetime import UTC, datetime, timedelta

import pytest

from paperctl.utils.time import parse_relative_time


def test_parse_now() -> None:
    """Test parsing 'now'."""
    result = parse_relative_time("now")
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC


def test_parse_iso_timestamp() -> None:
    """Test parsing ISO 8601 timestamps."""
    result = parse_relative_time("2024-01-01T00:00:00Z")
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 1


def test_parse_relative_hours() -> None:
    """Test parsing relative hours."""
    result = parse_relative_time("-1h")
    expected = datetime.now(UTC) - timedelta(hours=1)
    assert abs((result - expected).total_seconds()) < 2


def test_parse_relative_minutes() -> None:
    """Test parsing relative minutes."""
    result = parse_relative_time("-30m")
    expected = datetime.now(UTC) - timedelta(minutes=30)
    assert abs((result - expected).total_seconds()) < 2


def test_parse_relative_days() -> None:
    """Test parsing relative days."""
    result = parse_relative_time("-7d")
    expected = datetime.now(UTC) - timedelta(days=7)
    assert abs((result - expected).total_seconds()) < 2


def test_parse_natural_language() -> None:
    """Test parsing natural language times."""
    result = parse_relative_time("1 hour ago")
    expected = datetime.now(UTC) - timedelta(hours=1)
    assert abs((result - expected).total_seconds()) < 2


def test_parse_invalid() -> None:
    """Test parsing invalid time strings."""
    with pytest.raises(ValueError):
        parse_relative_time("invalid")

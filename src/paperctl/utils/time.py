"""Time parsing utilities."""

import re
from datetime import UTC, datetime, timedelta

from dateutil import parser as dateutil_parser


def parse_relative_time(time_str: str) -> datetime:
    """Parse a relative time string to datetime.

    Supports:
    - ISO 8601 timestamps
    - Relative times: -1h, -30m, -7d
    - Natural language: "1 hour ago", "2 days ago"
    - "now"

    Args:
        time_str: Time string to parse

    Returns:
        Datetime object in UTC

    Raises:
        ValueError: If time string cannot be parsed
    """
    time_str = time_str.strip()

    # Handle "now"
    if time_str.lower() == "now":
        return datetime.now(UTC)

    # Try ISO 8601 first
    try:
        dt = dateutil_parser.isoparse(time_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (ValueError, dateutil_parser.ParserError):
        pass

    # Try relative time format: -1h, -30m, -7d
    pattern = r"^(-?)(\d+)(h|m|d|s|w)$"
    match = re.match(pattern, time_str)
    if match:
        sign, amount, unit = match.groups()
        multiplier = -1 if sign == "-" else 1
        amount_int = int(amount) * multiplier

        unit_map = {
            "s": "seconds",
            "m": "minutes",
            "h": "hours",
            "d": "days",
            "w": "weeks",
        }

        delta = timedelta(**{unit_map[unit]: amount_int})
        return datetime.now(UTC) + delta

    # Try natural language: "1 hour ago", "2 days ago"
    pattern = r"^(\d+)\s+(second|minute|hour|day|week)s?\s+ago$"
    match = re.match(pattern, time_str, re.IGNORECASE)
    if match:
        amount, unit = match.groups()
        amount_int = int(amount)

        unit_map = {
            "second": "seconds",
            "minute": "minutes",
            "hour": "hours",
            "day": "days",
            "week": "weeks",
        }

        delta = timedelta(**{unit_map[unit.lower()]: amount_int})
        return datetime.now(UTC) - delta

    raise ValueError(f"Cannot parse time string: {time_str}")

"""JSON formatter for machine-readable output."""

import json
from typing import Any

from paperctl.client.models import Archive, Event, Group, System


class JSONFormatter:
    """Format output as JSON."""

    def format_events(self, events: list[Event]) -> str:
        """Format events as JSON.

        Args:
            events: Events to format

        Returns:
            JSON string
        """
        return json.dumps([e.model_dump(mode="json") for e in events], indent=2)

    def format_systems(self, systems: list[System]) -> str:
        """Format systems as JSON.

        Args:
            systems: Systems to format

        Returns:
            JSON string
        """
        return json.dumps([s.model_dump(mode="json") for s in systems], indent=2)

    def format_groups(self, groups: list[Group]) -> str:
        """Format groups as JSON.

        Args:
            groups: Groups to format

        Returns:
            JSON string
        """
        return json.dumps([g.model_dump(mode="json") for g in groups], indent=2)

    def format_archives(self, archives: list[Archive]) -> str:
        """Format archives as JSON.

        Args:
            archives: Archives to format

        Returns:
            JSON string
        """
        return json.dumps([a.model_dump(mode="json") for a in archives], indent=2)

    def format_any(self, data: Any) -> str:
        """Format any data as JSON.

        Args:
            data: Data to format

        Returns:
            JSON string
        """
        if hasattr(data, "model_dump"):
            return json.dumps(data.model_dump(mode="json"), indent=2)
        return json.dumps(data, indent=2, default=str)

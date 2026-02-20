"""JSON formatter for machine-readable output."""

import json
from typing import Any

from paperctl.client.models import Entity, Event


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

    def format_entities(self, entities: list[Entity]) -> str:
        """Format entities as JSON.

        Args:
            entities: Entities to format

        Returns:
            JSON string
        """
        return json.dumps([e.model_dump(mode="json") for e in entities], indent=2)

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

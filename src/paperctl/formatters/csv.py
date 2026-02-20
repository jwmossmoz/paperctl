"""CSV formatter for spreadsheet-friendly output."""

import csv
from io import StringIO

from paperctl.client.models import Entity, Event


class CSVFormatter:
    """Format output as CSV."""

    def format_events(self, events: list[Event]) -> str:
        """Format events as CSV.

        Args:
            events: Events to format

        Returns:
            CSV string
        """
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow(["time", "hostname", "program", "severity", "message"])

        for event in events:
            writer.writerow(
                [
                    event.time.isoformat(),
                    event.hostname,
                    event.program or "",
                    event.severity or "",
                    event.message,
                ]
            )

        return output.getvalue()

    def format_entities(self, entities: list[Entity]) -> str:
        """Format entities as CSV.

        Args:
            entities: Entities to format

        Returns:
            CSV string
        """
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow(["id", "type", "name", "display_name", "last_seen_time", "in_maintenance"])

        for entity in entities:
            writer.writerow(
                [
                    entity.id,
                    entity.type,
                    entity.name,
                    entity.display_name,
                    entity.last_seen_time.isoformat() if entity.last_seen_time else "",
                    entity.in_maintenance,
                ]
            )

        return output.getvalue()

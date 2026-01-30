"""CSV formatter for spreadsheet-friendly output."""

import csv
from io import StringIO

from paperctl.client.models import Archive, Event, Group, System


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

        # Header
        writer.writerow(
            [
                "id",
                "received_at",
                "source_name",
                "source_ip",
                "program",
                "severity",
                "facility",
                "message",
            ]
        )

        # Rows
        for event in events:
            writer.writerow(
                [
                    event.id,
                    event.received_at.isoformat(),
                    event.source_name,
                    event.source_ip or "",
                    event.program,
                    event.severity,
                    event.facility,
                    event.message,
                ]
            )

        return output.getvalue()

    def format_systems(self, systems: list[System]) -> str:
        """Format systems as CSV.

        Args:
            systems: Systems to format

        Returns:
            CSV string
        """
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["id", "name", "ip_address", "hostname", "last_event_at"])

        # Rows
        for system in systems:
            writer.writerow(
                [
                    system.id,
                    system.name,
                    system.ip_address or "",
                    system.hostname or "",
                    system.last_event_at.isoformat() if system.last_event_at else "",
                ]
            )

        return output.getvalue()

    def format_groups(self, groups: list[Group]) -> str:
        """Format groups as CSV.

        Args:
            groups: Groups to format

        Returns:
            CSV string
        """
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["id", "name", "system_count", "system_wildcard"])

        # Rows
        for group in groups:
            writer.writerow(
                [
                    group.id,
                    group.name,
                    len(group.systems),
                    group.system_wildcard or "",
                ]
            )

        return output.getvalue()

    def format_archives(self, archives: list[Archive]) -> str:
        """Format archives as CSV.

        Args:
            archives: Archives to format

        Returns:
            CSV string
        """
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["filename", "start", "end", "filesize"])

        # Rows
        for archive in archives:
            writer.writerow(
                [
                    archive.filename,
                    archive.start.isoformat(),
                    archive.end.isoformat(),
                    archive.filesize,
                ]
            )

        return output.getvalue()

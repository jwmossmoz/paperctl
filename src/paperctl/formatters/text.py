"""Text formatter for console output."""

from rich.console import Console
from rich.table import Table

from paperctl.client.models import Archive, Event, Group, System


class TextFormatter:
    """Format output as human-readable text."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize text formatter.

        Args:
            console: Rich console instance
        """
        self.console = console or Console()

    def format_event(self, event: Event) -> str:
        """Format a single event as text.

        Args:
            event: Event to format

        Returns:
            Formatted text
        """
        timestamp = event.display_received_at
        source = event.source_name
        program = event.program
        message = event.message
        return f"{timestamp} {source} {program}: {message}"

    def print_events(self, events: list[Event]) -> None:
        """Print events to console.

        Args:
            events: Events to print
        """
        for event in events:
            self.console.print(self.format_event(event))

    def print_systems(self, systems: list[System]) -> None:
        """Print systems table.

        Args:
            systems: Systems to print
        """
        table = Table(title="Systems")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("IP Address", style="yellow")
        table.add_column("Last Event", style="magenta")

        for system in systems:
            last_event = (
                system.last_event_at.strftime("%Y-%m-%d %H:%M:%S")
                if system.last_event_at
                else "N/A"
            )
            table.add_row(
                str(system.id),
                system.name,
                system.ip_address or "N/A",
                last_event,
            )

        self.console.print(table)

    def print_groups(self, groups: list[Group]) -> None:
        """Print groups table.

        Args:
            groups: Groups to print
        """
        table = Table(title="Groups")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Systems", style="yellow")

        for group in groups:
            system_count = len(group.systems)
            table.add_row(
                str(group.id),
                group.name,
                str(system_count),
            )

        self.console.print(table)

    def print_archives(self, archives: list[Archive]) -> None:
        """Print archives table.

        Args:
            archives: Archives to print
        """
        table = Table(title="Archives")
        table.add_column("Filename", style="cyan")
        table.add_column("Start", style="green")
        table.add_column("End", style="yellow")
        table.add_column("Size", style="magenta")

        for archive in archives:
            table.add_row(
                archive.filename,
                archive.start.strftime("%Y-%m-%d %H:%M:%S"),
                archive.end.strftime("%Y-%m-%d %H:%M:%S"),
                archive.formatted_filesize,
            )

        self.console.print(table)

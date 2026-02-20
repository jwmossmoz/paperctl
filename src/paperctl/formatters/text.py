"""Text formatter for console output."""

from rich.console import Console
from rich.table import Table

from paperctl.client.models import Entity, Event


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
        timestamp = event.time.strftime("%Y-%m-%d %H:%M:%S")
        hostname = event.hostname
        program = event.program or ""
        message = event.message
        return f"{timestamp} {hostname} {program}: {message}"

    def print_events(self, events: list[Event]) -> None:
        """Print events to console.

        Args:
            events: Events to print
        """
        for event in events:
            self.console.print(self.format_event(event))

    def print_entities(self, entities: list[Entity]) -> None:
        """Print entities table.

        Args:
            entities: Entities to print
        """
        table = Table(title="Entities")
        table.add_column("ID", style="cyan")
        table.add_column("Type", style="blue")
        table.add_column("Name", style="green")
        table.add_column("Last Seen", style="magenta")
        table.add_column("Maintenance", style="yellow")

        for entity in entities:
            last_seen = (
                entity.last_seen_time.strftime("%Y-%m-%d %H:%M:%S")
                if entity.last_seen_time
                else "N/A"
            )
            table.add_row(
                entity.id,
                entity.type,
                entity.name,
                last_seen,
                "Yes" if entity.in_maintenance else "No",
            )

        self.console.print(table)

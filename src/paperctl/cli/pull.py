"""Pull command - download logs from a system."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from paperctl.client import PapertrailClient
from paperctl.client.models import Event
from paperctl.config import get_settings
from paperctl.formatters import CSVFormatter, JSONFormatter
from paperctl.utils import parse_relative_time, retry_with_backoff

console = Console()


def pull_command(
    system: Annotated[str, typer.Argument(help="System name or ID")],
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Output file (default: stdout)")
    ] = None,
    since: Annotated[str, typer.Option("--since", help="Start time (default: -1h)")] = "-1h",
    until: Annotated[str | None, typer.Option("--until", help="End time (default: now)")] = None,
    format: Annotated[
        str, typer.Option("--format", "-f", help="Output format: text|json|csv")
    ] = "text",
    query: Annotated[str | None, typer.Option("--query", "-q", help="Search query")] = None,
    api_token: Annotated[
        str | None, typer.Option("--token", envvar="PAPERTRAIL_API_TOKEN", help="API token")
    ] = None,
) -> None:
    """Pull logs from a system and save locally.

    Examples:
        # Pull last hour of logs to stdout
        paperctl pull web-1

        # Pull logs to file
        paperctl pull web-1 --output logs.txt

        # Pull specific time range
        paperctl pull web-1 --since -24h --until -1h

        # Pull with query filter
        paperctl pull web-1 --query "error" --output errors.txt

        # Pull as JSON
        paperctl pull web-1 --format json --output logs.json
    """
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()

        # Parse time parameters
        min_time = parse_relative_time(since)
        max_time = parse_relative_time(until) if until else None

        with PapertrailClient(settings.api_token, timeout=settings.timeout) as client:
            # Resolve system ID
            system_id = None
            if system.isdigit():
                system_id = int(system)
            else:
                # Search by name
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    progress.add_task(description="Looking up system...", total=None)
                    systems = retry_with_backoff(client.list_systems)
                    matching = [s for s in systems if s.name == system]
                    if not matching:
                        console.print(f"[red]System not found: {system}[/red]")
                        console.print("\n[yellow]Available systems:[/yellow]")
                        for s in systems[:10]:
                            console.print(f"  - {s.name} (ID: {s.id})")
                        if len(systems) > 10:
                            console.print(f"  ... and {len(systems) - 10} more")
                        raise typer.Exit(1) from None
                    system_id = matching[0].id

            # Fetch all events
            events: list[Event] = []
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(description="Downloading logs...", total=None)

                def do_fetch() -> list[Event]:
                    result = list(
                        client.search_iter(
                            query=query,
                            system_id=system_id,
                            min_time=min_time,
                            max_time=max_time,
                        )
                    )
                    progress.update(task, description=f"Downloaded {len(result)} events")
                    return result

                events = retry_with_backoff(do_fetch)

            # Format and output
            if format == "text":
                if output:
                    with open(output, "w") as f:
                        for event in events:
                            timestamp = event.display_received_at
                            source = event.source_name
                            program = event.program
                            message = event.message
                            f.write(f"{timestamp} {source} {program}: {message}\n")
                    console.print(f"[green]Wrote {len(events)} events to {output}[/green]")
                else:
                    for event in events:
                        timestamp = event.display_received_at
                        source = event.source_name
                        program = event.program
                        message = event.message
                        print(f"{timestamp} {source} {program}: {message}")
            elif format == "json":
                json_formatter = JSONFormatter()
                result = json_formatter.format_events(events)
                if output:
                    output.write_text(result)
                    console.print(f"[green]Wrote {len(events)} events to {output}[/green]")
                else:
                    print(result)
            elif format == "csv":
                csv_formatter = CSVFormatter()
                result = csv_formatter.format_events(events)
                if output:
                    output.write_text(result)
                    console.print(f"[green]Wrote {len(events)} events to {output}[/green]")
                else:
                    print(result)
            else:
                console.print(f"[red]Invalid format: {format}[/red]")
                raise typer.Exit(1) from None

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None

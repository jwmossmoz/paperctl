"""Search command implementation."""

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from paperctl.client import PapertrailClient
from paperctl.config import get_settings
from paperctl.formatters import CSVFormatter, JSONFormatter, TextFormatter
from paperctl.utils import parse_relative_time, retry_with_backoff

console = Console()


def search_command(
    query: Annotated[str | None, typer.Argument(help="Search query")] = None,
    system: Annotated[str | None, typer.Option("--system", "-s", help="Filter by system name or ID")] = None,
    group: Annotated[str | None, typer.Option("--group", "-g", help="Filter by group name or ID")] = None,
    since: Annotated[str | None, typer.Option("--since", help="Start time (e.g., -1h, 2024-01-01T00:00:00Z)")] = None,
    until: Annotated[str | None, typer.Option("--until", help="End time (e.g., now, -30m)")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n", help="Maximum events to return")] = 1000,
    follow: Annotated[bool, typer.Option("--follow", "-f", help="Tail mode (continuous streaming)")] = False,
    output: Annotated[str, typer.Option("--output", "-o", help="Output format")] = "text",
    file: Annotated[Path | None, typer.Option("--file", "-F", help="Write output to file")] = None,
    api_token: Annotated[str | None, typer.Option("--token", envvar="PAPERTRAIL_API_TOKEN", help="API token")] = None,
) -> None:
    """Search Papertrail logs.

    Examples:
        paperctl search "error" --since -1h
        paperctl search --system web-1 --output json
        paperctl search "status=500" --since "2024-01-01T00:00:00Z" --until now
    """
    try:
        # Load settings
        settings = get_settings(api_token=api_token) if api_token else get_settings()

        # Parse time parameters
        min_time = parse_relative_time(since) if since else None
        max_time = parse_relative_time(until) if until else None

        # Create client
        with PapertrailClient(settings.api_token, timeout=settings.timeout) as client:
            # Resolve system/group IDs
            system_id = None
            group_id = None

            if system:
                if system.isdigit():
                    system_id = int(system)
                else:
                    # Search by name
                    systems = client.list_systems()
                    matching = [s for s in systems if s.name == system]
                    if not matching:
                        console.print(f"[red]System not found: {system}[/red]")
                        raise typer.Exit(1) from None
                    system_id = matching[0].id

            if group:
                if group.isdigit():
                    group_id = int(group)
                else:
                    # Search by name
                    groups = client.list_groups()
                    matching = [g for g in groups if g.name == group]
                    if not matching:
                        console.print(f"[red]Group not found: {group}[/red]")
                        raise typer.Exit(1) from None
                    group_id = matching[0].id

            # Search with retry on rate limits
            def do_search():
                if follow:
                    # Tail mode - not yet implemented
                    console.print("[yellow]Tail mode not yet implemented[/yellow]")
                    raise typer.Exit(1) from None
                else:
                    return list(
                        client.search_iter(
                            query=query,
                            system_id=system_id,
                            group_id=group_id,
                            min_time=min_time,
                            max_time=max_time,
                            limit=limit,
                        )
                    )

            events = retry_with_backoff(do_search)

            # Format output
            if output == "text":
                formatter = TextFormatter(console)
                if file:
                    with open(file, "w") as f:
                        for event in events:
                            f.write(formatter.format_event(event) + "\n")
                    console.print(f"[green]Wrote {len(events)} events to {file}[/green]")
                else:
                    formatter.print_events(events)
            elif output == "json":
                formatter = JSONFormatter()
                result = formatter.format_events(events)
                if file:
                    file.write_text(result)
                    console.print(f"[green]Wrote {len(events)} events to {file}[/green]")
                else:
                    console.print(result)
            elif output == "csv":
                formatter = CSVFormatter()
                result = formatter.format_events(events)
                if file:
                    file.write_text(result)
                    console.print(f"[green]Wrote {len(events)} events to {file}[/green]")
                else:
                    console.print(result)
            else:
                console.print(f"[red]Invalid output format: {output}[/red]")
                raise typer.Exit(1) from None

            if not file:
                console.print(f"\n[dim]Total events: {len(events)}[/dim]", file=sys.stderr)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


def tail_command(
    query: Annotated[str | None, typer.Argument(help="Search query")] = None,
    system: Annotated[str | None, typer.Option("--system", "-s", help="Filter by system name or ID")] = None,
    group: Annotated[str | None, typer.Option("--group", "-g", help="Filter by group name or ID")] = None,
    output: Annotated[str, typer.Option("--output", "-o", help="Output format")] = "text",
    api_token: Annotated[str | None, typer.Option("--token", envvar="PAPERTRAIL_API_TOKEN", help="API token")] = None,
) -> None:
    """Tail Papertrail logs (alias for search --follow).

    Examples:
        paperctl tail "error"
        paperctl tail --system web-1
    """
    search_command(
        query=query,
        system=system,
        group=group,
        since=None,
        until=None,
        limit=1000,
        follow=True,
        output=output,
        file=None,
        api_token=api_token,
    )

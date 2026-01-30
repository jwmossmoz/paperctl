"""Search command implementation."""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console

from paperctl.client import PapertrailClient
from paperctl.config import get_settings
from paperctl.formatters import TextFormatter
from paperctl.utils import parse_relative_time, retry_with_backoff

if TYPE_CHECKING:
    from paperctl.client.models import Group

console = Console()


def search_command(
    query: Annotated[
        str | None,
        typer.Argument(help="Search query (text matching with AND/OR/NOT, no regex/wildcards)"),
    ] = None,
    system: Annotated[
        str | None, typer.Option("--system", "-s", help="Filter by system name or ID")
    ] = None,
    group: Annotated[
        str | None, typer.Option("--group", "-g", help="Filter by group name or ID")
    ] = None,
    since: Annotated[
        str | None, typer.Option("--since", help="Start time (e.g., -1h, 2024-01-01T00:00:00Z)")
    ] = None,
    until: Annotated[str | None, typer.Option("--until", help="End time (e.g., now, -30m)")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n", help="Maximum events to return")] = 1000,
    follow: Annotated[
        bool, typer.Option("--follow", "-f", help="Tail mode (continuous streaming)")
    ] = False,
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output format: text|json|csv")
    ] = "text",
    file: Annotated[
        pathlib.Path | None, typer.Option("--file", "-F", help="Write output to file")
    ] = None,
    api_token: Annotated[
        str | None, typer.Option("--token", envvar="PAPERTRAIL_API_TOKEN", help="API token")
    ] = None,
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
        if file is not None:
            file = pathlib.Path(file)

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
                    systems = retry_with_backoff(client.list_systems)
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
                    groups = retry_with_backoff(client.list_groups)
                    matching_groups: list[Group] = [g for g in groups if g.name == group]
                    if not matching_groups:
                        console.print(f"[red]Group not found: {group}[/red]")
                        raise typer.Exit(1) from None
                    group_id = matching_groups[0].id

            if follow:
                # Tail mode - not yet implemented
                console.print("[yellow]Tail mode not yet implemented[/yellow]")
                raise typer.Exit(1) from None

            if limit <= 0:
                console.print("[yellow]Limit must be greater than 0[/yellow]")
                raise typer.Exit(1) from None

            events = client.search_iter(
                query=query,
                system_id=system_id,
                group_id=group_id,
                min_time=min_time,
                max_time=max_time,
                total_limit=limit,
            )

            # Format output
            if output == "text":
                text_formatter = TextFormatter(console)
                event_count = 0
                if file:
                    with open(file, "w", encoding="utf-8") as handle:
                        for event in events:
                            handle.write(text_formatter.format_event(event) + "\n")
                            event_count += 1
                    console.print(f"[green]Wrote {event_count} events to {file}[/green]")
                else:
                    for event in events:
                        console.print(text_formatter.format_event(event))
                        event_count += 1
            elif output == "json":
                import json

                event_count = 0
                if file:
                    with open(file, "w", encoding="utf-8") as handle:
                        handle.write("[")
                        first = True
                        for event in events:
                            if not first:
                                handle.write(",\n")
                            handle.write(json.dumps(event.model_dump(mode="json")))
                            first = False
                            event_count += 1
                        handle.write("]\n")
                    console.print(f"[green]Wrote {event_count} events to {file}[/green]")
                else:
                    import sys as _sys

                    _sys.stdout.write("[")
                    first = True
                    for event in events:
                        if not first:
                            _sys.stdout.write(",\n")
                        _sys.stdout.write(json.dumps(event.model_dump(mode="json")))
                        first = False
                        event_count += 1
                    _sys.stdout.write("]\n")
            elif output == "csv":
                import csv
                import sys as _sys

                event_count = 0
                if file:
                    with open(file, "w", encoding="utf-8", newline="") as handle:
                        writer = csv.writer(handle)
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
                            event_count += 1
                    console.print(f"[green]Wrote {event_count} events to {file}[/green]")
                else:
                    writer = csv.writer(_sys.stdout)
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
                        event_count += 1
            else:
                console.print(f"[red]Invalid output format: {output}[/red]")
                raise typer.Exit(1) from None

            if not file:
                import sys as _sys

                _sys.stderr.write(f"\nTotal events: {event_count}\n")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


def tail_command(
    query: Annotated[
        str | None,
        typer.Argument(help="Search query (text matching with AND/OR/NOT, no regex/wildcards)"),
    ] = None,
    system: Annotated[
        str | None, typer.Option("--system", "-s", help="Filter by system name or ID")
    ] = None,
    group: Annotated[
        str | None, typer.Option("--group", "-g", help="Filter by group name or ID")
    ] = None,
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output format: text|json|csv")
    ] = "text",
    api_token: Annotated[
        str | None, typer.Option("--token", envvar="PAPERTRAIL_API_TOKEN", help="API token")
    ] = None,
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

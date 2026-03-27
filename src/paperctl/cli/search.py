"""Search command implementation."""

from __future__ import annotations

import pathlib
from typing import Annotated

import typer
from rich.console import Console

from paperctl.client import SWOClient
from paperctl.config import get_settings
from paperctl.formatters import TextFormatter
from paperctl.utils import parse_relative_time, retry_with_backoff

console = Console()


def search_command(
    query: Annotated[
        str | None,
        typer.Argument(help="Search query (text matching with AND/OR/NOT, no regex/wildcards)"),
    ] = None,
    system: Annotated[
        str | None, typer.Option("--system", "-s", help="Filter by system name")
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
        str | None,
        typer.Option(
            "--token",
            envvar="SWO_API_TOKEN",
            help="API token (SWO_API_TOKEN or legacy PAPERTRAIL_API_TOKEN)",
        ),
    ] = None,
) -> None:
    """Search SolarWinds Observability logs.

    Examples:
        paperctl search "error" --since -1h
        paperctl search --system web-1 --output json
        paperctl search "status=500" --since "2024-01-01T00:00:00Z" --until now
    """
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()

        start_time = parse_relative_time(since) if since else None
        end_time = parse_relative_time(until) if until else None
        if file is not None:
            file = pathlib.Path(file)

        with SWOClient(
            settings.api_token, api_url=settings.api_url, timeout=settings.timeout
        ) as client:
            # Resolve hostname via entities API
            hostname: str | None = None

            if system:
                entities = retry_with_backoff(lambda: client.list_entities(entity_type="Host"))
                matching = [e for e in entities if e.name == system]
                if not matching:
                    # Try partial match
                    matching = [e for e in entities if system.lower() in e.name.lower()]
                if not matching:
                    console.print(f"[red]System not found: {system}[/red]")
                    raise typer.Exit(1) from None
                if len(matching) > 1:
                    console.print(f"[yellow]Multiple systems match '{system}':[/yellow]")
                    for e in matching[:10]:
                        console.print(f"  - {e.name}")
                    raise typer.Exit(1) from None
                hostname = matching[0].name

            if follow:
                console.print("[yellow]Tail mode not yet implemented[/yellow]")
                raise typer.Exit(1) from None

            if limit <= 0:
                console.print("[yellow]Limit must be greater than 0[/yellow]")
                raise typer.Exit(1) from None

            events = client.logs_iter(
                filter_query=query,
                hostname=hostname,
                start_time=start_time,
                end_time=end_time,
                total_limit=limit,
            )

            event_count = 0

            if output == "text":
                text_formatter = TextFormatter(console)
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

                headers = ["time", "hostname", "program", "severity", "message"]

                if file:
                    with open(file, "w", encoding="utf-8", newline="") as handle:
                        writer = csv.writer(handle)
                        writer.writerow(headers)
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
                            event_count += 1
                    console.print(f"[green]Wrote {event_count} events to {file}[/green]")
                else:
                    writer = csv.writer(_sys.stdout)
                    writer.writerow(headers)
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
        str | None, typer.Option("--system", "-s", help="Filter by system name")
    ] = None,
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output format: text|json|csv")
    ] = "text",
    api_token: Annotated[
        str | None,
        typer.Option(
            "--token",
            envvar="SWO_API_TOKEN",
            help="API token (SWO_API_TOKEN or legacy PAPERTRAIL_API_TOKEN)",
        ),
    ] = None,
) -> None:
    """Tail SolarWinds Observability logs (alias for search --follow).

    Examples:
        paperctl tail "error"
        paperctl tail --system web-1
    """
    search_command(
        query=query,
        system=system,
        since=None,
        until=None,
        limit=1000,
        follow=True,
        output=output,
        file=None,
        api_token=api_token,
    )

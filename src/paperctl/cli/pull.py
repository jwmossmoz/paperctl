"""Pull command - download logs from systems."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn

from paperctl.client import PapertrailClient
from paperctl.client.async_api import AsyncPapertrailClient
from paperctl.client.models import Event
from paperctl.config import get_settings
from paperctl.formatters import CSVFormatter, JSONFormatter
from paperctl.utils import RateLimiter, parse_relative_time, retry_with_backoff

console = Console()


def pull_command(
    systems: Annotated[str, typer.Argument(help="System name(s) or ID(s), comma-separated")],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output directory or file (default: ~/.cache/paperctl/logs/<system>)",
        ),
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
    """Pull logs from one or more systems.

    Examples:
        # Single system
        paperctl pull web-1

        # Multiple systems (parallel with rate limiting)
        paperctl pull web-1,web-2,web-3 --output logs/

        # Multiple systems with query
        paperctl pull web-1,web-2 --query "error" --output errors/

        # Specific time range
        paperctl pull web-1 --since -24h --until -1h --output logs.txt
    """
    system_list = [s.strip() for s in systems.split(",")]

    if len(system_list) == 1:
        # Single system - use sync implementation
        _pull_single_system(
            system=system_list[0],
            output=output,
            since=since,
            until=until,
            format=format,
            query=query,
            api_token=api_token,
        )
    else:
        # Multiple systems - use async parallel implementation
        asyncio.run(
            _pull_multiple_systems(
                systems=system_list,
                output_dir=output,
                since=since,
                until=until,
                format=format,
                query=query,
                api_token=api_token,
            )
        )


def _pull_single_system(
    system: str,
    output: Path | None,
    since: str,
    until: str | None,
    format: str,
    query: str | None,
    api_token: str | None,
) -> None:
    """Pull logs from a single system (sync)."""
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()
        min_time = parse_relative_time(since)
        max_time = parse_relative_time(until) if until else None

        with PapertrailClient(settings.api_token, timeout=settings.timeout) as client:
            # Resolve system ID
            system_id = _resolve_system_id(client, system)

            # Fetch events
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

            _write_output(system, events, output, format)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


async def _pull_multiple_systems(
    systems: list[str],
    output_dir: Path | None,
    since: str,
    until: str | None,
    format: str,
    query: str | None,
    api_token: str | None,
) -> None:
    """Pull logs from multiple systems in parallel with rate limiting."""
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()
        min_time = parse_relative_time(since)
        max_time = parse_relative_time(until) if until else None

        # Create output directory if specified
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

        async with AsyncPapertrailClient(settings.api_token, timeout=settings.timeout) as client:
            # Resolve system IDs
            console.print("Looking up systems...")
            system_list = await client.list_systems()
            system_map = {s.name: s.id for s in system_list}
            system_map.update({str(s.id): s.id for s in system_list})

            system_ids = []
            for system in systems:
                if system in system_map:
                    system_ids.append((system, system_map[system]))
                else:
                    console.print(
                        f"[yellow]Warning: System '{system}' not found, skipping[/yellow]"
                    )

            if not system_ids:
                console.print("[red]No valid systems found[/red]")
                raise typer.Exit(1)

            # Fetch logs in parallel with rate limiting
            rate_limiter = RateLimiter(max_requests=25, window_seconds=5.0)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                tasks = {}
                for system_name, _ in system_ids:
                    tasks[system_name] = progress.add_task(
                        description=f"{system_name}: Starting...", total=None
                    )

                async def fetch_system(
                    system_name: str, system_id: int, task_id: TaskID
                ) -> tuple[str, list[Event]]:
                    events: list[Event] = []
                    async for event in client.search_iter(
                        query=query,
                        system_id=system_id,
                        min_time=min_time,
                        max_time=max_time,
                    ):
                        await rate_limiter.acquire()
                        events.append(event)
                        if len(events) % 100 == 0:
                            progress.update(
                                task_id, description=f"{system_name}: {len(events)} events"
                            )

                    progress.update(task_id, description=f"{system_name}: {len(events)} events ✓")
                    return system_name, events

                results = await asyncio.gather(
                    *[
                        fetch_system(system_name, system_id, tasks[system_name])
                        for system_name, system_id in system_ids
                    ]
                )

            # Write outputs
            for system_name, events in results:
                if output_dir:
                    ext = {"text": "txt", "json": "json", "csv": "csv"}[format]
                    output_file = output_dir / f"{system_name}.{ext}"
                    _write_output(system_name, events, output_file, format)
                else:
                    _write_output(system_name, events, None, format)

            total_events = sum(len(events) for _, events in results)
            console.print(
                f"\n[green]Downloaded {total_events} total events from {len(results)} systems[/green]"
            )

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


def _resolve_system_id(client: PapertrailClient, system: str) -> int:
    """Resolve system name to ID."""
    if system.isdigit():
        return int(system)

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
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
            raise typer.Exit(1)
        return matching[0].id


def _write_output(system: str, events: list[Event], output: Path | None, format: str) -> None:
    """Write events to output."""
    # Default to cache directory if no output specified
    if output is None:
        cache_dir = Path.home() / ".cache" / "paperctl" / "logs"
        cache_dir.mkdir(parents=True, exist_ok=True)
        ext = {"text": "txt", "json": "json", "csv": "csv"}[format]
        output = cache_dir / f"{system}.{ext}"

    if format == "text":
        if output:
            with open(output, "w") as f:
                for event in events:
                    timestamp = event.display_received_at
                    source = event.source_name
                    program = event.program
                    message = event.message
                    f.write(f"{timestamp} {source} {program}: {message}\n")
            console.print(f"[green]{system}: Wrote {len(events)} events to {output}[/green]")
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
            console.print(f"[green]{system}: Wrote {len(events)} events to {output}[/green]")
        else:
            print(result)
    elif format == "csv":
        csv_formatter = CSVFormatter()
        result = csv_formatter.format_events(events)
        if output:
            output.write_text(result)
            console.print(f"[green]{system}: Wrote {len(events)} events to {output}[/green]")
        else:
            print(result)
    else:
        console.print(f"[red]Invalid format: {format}[/red]")
        raise typer.Exit(1)

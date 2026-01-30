"""Pull command - download logs from systems."""

import asyncio
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Annotated, TextIO

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn

from paperctl.client import PapertrailClient
from paperctl.client.async_api import AsyncPapertrailClient
from paperctl.client.models import Event, System
from paperctl.config import get_settings
from paperctl.utils import AsyncRateLimiter, parse_relative_time, retry_with_backoff

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
    since: Annotated[
        str | None, typer.Option("--since", help="Start time (default: all logs)")
    ] = None,
    until: Annotated[str | None, typer.Option("--until", help="End time (default: now)")] = None,
    format: Annotated[
        str, typer.Option("--format", "-f", help="Output format: text|json|csv")
    ] = "text",
    query: Annotated[
        str | None,
        typer.Option(
            "--query",
            "-q",
            help="Search query (text matching with AND/OR/NOT, no regex/wildcards)",
        ),
    ] = None,
    api_token: Annotated[
        str | None, typer.Option("--token", envvar="PAPERTRAIL_API_TOKEN", help="API token")
    ] = None,
) -> None:
    """Pull logs from one or more systems.

    System names support partial matching - you can use Taskcluster worker IDs
    like 'vm-abc123' and it will match 'vm-abc123.reddog.microsoft.com'.

    Examples:
        # Single system (downloads all available logs)
        paperctl pull web-1

        # Partial name matching (matches vm-abc123.reddog.microsoft.com)
        paperctl pull vm-abc123

        # Multiple systems (parallel with rate limiting)
        paperctl pull web-1,web-2,web-3 --output logs/

        # Last 24 hours only
        paperctl pull web-1 --since -24h

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
    since: str | None,
    until: str | None,
    format: str,
    query: str | None,
    api_token: str | None,
) -> None:
    """Pull logs from a single system (sync)."""
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()
        min_time = parse_relative_time(since) if since else None
        max_time = parse_relative_time(until) if until else None

        with PapertrailClient(settings.api_token, timeout=settings.timeout) as client:
            # Resolve system ID (supports partial matching)
            system_id, resolved_name, was_partial = _resolve_system_id(client, system)
            if was_partial:
                console.print(f"[dim]Matched '{system}' → {resolved_name}[/dim]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(description="Downloading logs...", total=None)
                events = client.search_iter(
                    query=query,
                    system_id=system_id,
                    min_time=min_time,
                    max_time=max_time,
                )

                def update_progress(count: int) -> None:
                    progress.update(task, description=f"Downloaded {count} events")

                _write_output(resolved_name, events, output, format, update_progress)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


async def _pull_multiple_systems(
    systems: list[str],
    output_dir: Path | None,
    since: str | None,
    until: str | None,
    format: str,
    query: str | None,
    api_token: str | None,
) -> None:
    """Pull logs from multiple systems in parallel with rate limiting."""
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()
        min_time = parse_relative_time(since) if since else None
        max_time = parse_relative_time(until) if until else None

        # Create output directory if specified
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

        rate_limiter = AsyncRateLimiter(max_requests=25, window_seconds=5.0)
        async with AsyncPapertrailClient(
            settings.api_token, timeout=settings.timeout, rate_limiter=rate_limiter
        ) as client:
            # Resolve system IDs with partial matching support
            console.print("Looking up systems...")
            system_list = await client.list_systems()

            system_ids = []
            for system in systems:
                resolved = _resolve_system_from_list(system, system_list)
                if resolved:
                    system_id, resolved_name = resolved
                    system_ids.append((resolved_name, system_id))
                    if resolved_name != system:
                        console.print(f"[dim]Matched '{system}' → {resolved_name}[/dim]")
                else:
                    console.print(
                        f"[yellow]Warning: System '{system}' not found, skipping[/yellow]"
                    )

            if not system_ids:
                console.print("[red]No valid systems found[/red]")
                raise typer.Exit(1)

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
                ) -> tuple[str, int, Path]:
                    output_path = _resolve_output_path(system_name, output_dir, format)
                    event_count = 0
                    finalize = None
                    with open(output_path, "w", encoding="utf-8", newline="") as handle:
                        if format == "text":
                            write_event = _text_event_writer(handle)
                        elif format == "json":
                            write_event = _json_event_writer(handle)
                            finalize = _finalize_json
                        elif format == "csv":
                            write_event = _csv_event_writer(handle)
                        else:
                            console.print(f"[red]Invalid format: {format}[/red]")
                            raise typer.Exit(1)

                        try:
                            async for event in client.search_iter(
                                query=query,
                                system_id=system_id,
                                min_time=min_time,
                                max_time=max_time,
                            ):
                                write_event(event)
                                event_count += 1
                                if event_count % 100 == 0:
                                    progress.update(
                                        task_id,
                                        description=f"{system_name}: {event_count} events",
                                    )
                        finally:
                            if finalize is not None:
                                finalize(handle)

                    progress.update(task_id, description=f"{system_name}: {event_count} events ✓")
                    return system_name, event_count, output_path

                results = await asyncio.gather(
                    *[
                        fetch_system(system_name, system_id, tasks[system_name])
                        for system_name, system_id in system_ids
                    ]
                )

            total_events = sum(event_count for _, event_count, _ in results)
            for system_name, event_count, output_path in results:
                console.print(
                    f"[green]{system_name}: Wrote {event_count} events to {output_path}[/green]"
                )
            console.print(
                f"\n[green]Downloaded {total_events} total events from {len(results)} systems[/green]"
            )

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


def _resolve_system_id(client: PapertrailClient, system: str) -> tuple[int, str, bool]:
    """Resolve system name to ID with partial matching support.

    Returns:
        Tuple of (system_id, resolved_system_name, was_partial_match)
    """
    if system.isdigit():
        return int(system), system, False

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        progress.add_task(description="Looking up system...", total=None)
        systems = retry_with_backoff(client.list_systems)

    # Try exact match first
    exact = [s for s in systems if s.name == system]
    if exact:
        return exact[0].id, exact[0].name, False

    # Try partial/substring match (case-insensitive)
    partial = [s for s in systems if system.lower() in s.name.lower()]

    if not partial:
        console.print(f"[red]System not found: {system}[/red]")
        console.print("\n[yellow]Available systems:[/yellow]")
        for s in systems[:10]:
            console.print(f"  - {s.name} (ID: {s.id})")
        if len(systems) > 10:
            console.print(f"  ... and {len(systems) - 10} more")
        raise typer.Exit(1)

    if len(partial) == 1:
        matched = partial[0]
        return matched.id, matched.name, True

    # Multiple matches - show them
    console.print(f"[yellow]Multiple systems match '{system}':[/yellow]")
    for s in partial[:10]:
        console.print(f"  - {s.name} (ID: {s.id})")
    if len(partial) > 10:
        console.print(f"  ... and {len(partial) - 10} more")
    console.print("\n[yellow]Please provide a more specific name or use the system ID.[/yellow]")
    raise typer.Exit(1)


def _resolve_system_from_list(system: str, systems: list[System]) -> tuple[int, str] | None:
    """Resolve system name to ID from a pre-fetched list.

    Supports:
    - Exact name match
    - Numeric ID
    - Partial/substring match (case-insensitive)

    Returns:
        Tuple of (system_id, resolved_name) or None if not found/ambiguous
    """
    # Try numeric ID
    if system.isdigit():
        system_id = int(system)
        for s in systems:
            if s.id == system_id:
                return s.id, s.name
        return None

    # Try exact match
    for s in systems:
        if s.name == system:
            return s.id, s.name

    # Try partial/substring match (case-insensitive)
    partial = [s for s in systems if system.lower() in s.name.lower()]

    if len(partial) == 1:
        return partial[0].id, partial[0].name

    # No match or ambiguous (multiple matches for multi-system, we skip ambiguous)
    return None


def _resolve_output_path(system: str, output: Path | None, format: str) -> Path:
    """Resolve output path, defaulting to cache directory when unset."""
    if output is None:
        cache_dir = Path.home() / ".cache" / "paperctl" / "logs"
        cache_dir.mkdir(parents=True, exist_ok=True)
        ext = {"text": "txt", "json": "json", "csv": "csv"}[format]
        return cache_dir / f"{system}.{ext}"

    if output.is_dir():
        ext = {"text": "txt", "json": "json", "csv": "csv"}[format]
        return output / f"{system}.{ext}"

    return output


def _text_event_writer(handle: TextIO) -> Callable[[Event], None]:
    def write_event(event: Event) -> None:
        timestamp = event.display_received_at
        source = event.source_name
        program = event.program
        message = event.message
        handle.write(f"{timestamp} {source} {program}: {message}\n")

    return write_event


def _json_event_writer(handle: TextIO) -> Callable[[Event], None]:
    import json

    handle.write("[")
    first = True

    def write_event(event: Event) -> None:
        nonlocal first
        if not first:
            handle.write(",\n")
        handle.write(json.dumps(event.model_dump(mode="json")))
        first = False

    return write_event


def _csv_event_writer(handle: TextIO) -> Callable[[Event], None]:
    import csv

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

    def write_event(event: Event) -> None:
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

    return write_event


def _finalize_json(handle: TextIO) -> None:
    handle.write("]\n")


def _write_output(
    system: str,
    events: Iterable[Event],
    output: Path | None,
    format: str,
    progress_callback: Callable[[int], None] | None = None,
) -> None:
    """Write events to output."""
    output_path = _resolve_output_path(system, output, format)
    event_count = 0

    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        if format == "text":
            write_event = _text_event_writer(handle)
        elif format == "json":
            write_event = _json_event_writer(handle)
        elif format == "csv":
            write_event = _csv_event_writer(handle)
        else:
            console.print(f"[red]Invalid format: {format}[/red]")
            raise typer.Exit(1)

        for event in events:
            write_event(event)
            event_count += 1
            if progress_callback and event_count % 100 == 0:
                progress_callback(event_count)

        if format == "json":
            handle.write("]\n")

    if progress_callback:
        progress_callback(event_count)
    console.print(f"[green]{system}: Wrote {event_count} events to {output_path}[/green]")

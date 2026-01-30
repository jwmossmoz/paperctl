"""Systems command implementation."""

from typing import Annotated

import typer
from rich.console import Console

from paperctl.client import PapertrailClient
from paperctl.config import get_settings
from paperctl.formatters import CSVFormatter, JSONFormatter, TextFormatter
from paperctl.utils import retry_with_backoff

console = Console()

systems_app = typer.Typer(name="systems", help="Manage systems")


@systems_app.command("list")
def list_systems(
    output: Annotated[str, typer.Option("--output", "-o", help="Output format")] = "text",
    api_token: Annotated[str | None, typer.Option("--token", envvar="PAPERTRAIL_API_TOKEN", help="API token")] = None,
) -> None:
    """List all systems.

    Examples:
        paperctl systems list
        paperctl systems list --output json
    """
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()

        with PapertrailClient(settings.api_token, timeout=settings.timeout) as client:
            systems = retry_with_backoff(client.list_systems)

            if output == "text":
                formatter = TextFormatter(console)
                formatter.print_systems(systems)
            elif output == "json":
                formatter = JSONFormatter()
                console.print(formatter.format_systems(systems))
            elif output == "csv":
                formatter = CSVFormatter()
                console.print(formatter.format_systems(systems))
            else:
                console.print(f"[red]Invalid output format: {output}[/red]")
                raise typer.Exit(1) from None

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@systems_app.command("show")
def show_system(
    system_id: Annotated[int, typer.Argument(help="System ID")],
    output: Annotated[str, typer.Option("--output", "-o", help="Output format")] = "text",
    api_token: Annotated[str | None, typer.Option("--token", envvar="PAPERTRAIL_API_TOKEN", help="API token")] = None,
) -> None:
    """Show system details.

    Examples:
        paperctl systems show 12345
        paperctl systems show 12345 --output json
    """
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()

        with PapertrailClient(settings.api_token, timeout=settings.timeout) as client:
            system = retry_with_backoff(lambda: client.get_system(system_id))

            if output == "text":
                console.print(f"[bold]System {system.id}[/bold]")
                console.print(f"Name: {system.name}")
                console.print(f"IP Address: {system.ip_address or 'N/A'}")
                console.print(f"Hostname: {system.hostname or 'N/A'}")
                console.print(f"Syslog Hostname: {system.syslog_hostname or 'N/A'}")
                if system.last_event_at:
                    console.print(f"Last Event: {system.last_event_at}")
            elif output == "json":
                formatter = JSONFormatter()
                console.print(formatter.format_any(system))
            elif output == "csv":
                formatter = CSVFormatter()
                console.print(formatter.format_systems([system]))
            else:
                console.print(f"[red]Invalid output format: {output}[/red]")
                raise typer.Exit(1) from None

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None

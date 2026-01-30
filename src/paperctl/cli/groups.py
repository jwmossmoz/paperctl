"""Groups command implementation."""

from typing import Annotated

import typer
from rich.console import Console

from paperctl.client import PapertrailClient
from paperctl.config import get_settings
from paperctl.formatters import CSVFormatter, JSONFormatter, TextFormatter
from paperctl.utils import retry_with_backoff

console = Console()

groups_app = typer.Typer(name="groups", help="Manage groups")


@groups_app.command("list")
def list_groups(
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output format: text|json|csv")
    ] = "text",
    api_token: Annotated[
        str | None, typer.Option("--token", envvar="PAPERTRAIL_API_TOKEN", help="API token")
    ] = None,
) -> None:
    """List all groups.

    Examples:
        paperctl groups list
        paperctl groups list --output json
    """
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()

        with PapertrailClient(settings.api_token, timeout=settings.timeout) as client:
            groups = retry_with_backoff(client.list_groups)

            if output == "text":
                text_formatter = TextFormatter(console)
                text_formatter.print_groups(groups)
            elif output == "json":
                json_formatter = JSONFormatter()
                console.print(json_formatter.format_groups(groups))
            elif output == "csv":
                csv_formatter = CSVFormatter()
                console.print(csv_formatter.format_groups(groups))
            else:
                console.print(f"[red]Invalid output format: {output}[/red]")
                raise typer.Exit(1) from None

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@groups_app.command("show")
def show_group(
    group_id: Annotated[int, typer.Argument(help="Group ID")],
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output format: text|json|csv")
    ] = "text",
    api_token: Annotated[
        str | None, typer.Option("--token", envvar="PAPERTRAIL_API_TOKEN", help="API token")
    ] = None,
) -> None:
    """Show group details with systems.

    Examples:
        paperctl groups show 12345
        paperctl groups show 12345 --output json
    """
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()

        with PapertrailClient(settings.api_token, timeout=settings.timeout) as client:
            group = retry_with_backoff(lambda: client.get_group(group_id))

            if output == "text":
                console.print(f"[bold]Group {group.id}[/bold]")
                console.print(f"Name: {group.name}")
                console.print(f"System Wildcard: {group.system_wildcard or 'N/A'}")
                console.print(f"\n[bold]Systems ({len(group.systems)}):[/bold]")
                if group.systems:
                    text_formatter = TextFormatter(console)
                    text_formatter.print_systems(group.systems)
                else:
                    console.print("[dim]No systems[/dim]")
            elif output == "json":
                json_formatter = JSONFormatter()
                console.print(json_formatter.format_any(group))
            elif output == "csv":
                csv_formatter = CSVFormatter()
                console.print(csv_formatter.format_groups([group]))
            else:
                console.print(f"[red]Invalid output format: {output}[/red]")
                raise typer.Exit(1) from None

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None

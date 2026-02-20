"""Entities command implementation."""

from typing import Annotated

import typer
from rich.console import Console

from paperctl.client import SWOClient
from paperctl.config import get_settings
from paperctl.formatters import CSVFormatter, JSONFormatter, TextFormatter
from paperctl.utils import retry_with_backoff

console = Console()

entities_app = typer.Typer(name="entities", help="Manage entities")


@entities_app.command("list")
def list_entities(
    entity_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Entity type (e.g., Host)"),
    ] = "Host",
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Filter by name"),
    ] = None,
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output format: text|json|csv")
    ] = "text",
    api_token: Annotated[
        str | None, typer.Option("--token", envvar="SWO_API_TOKEN", help="API token")
    ] = None,
) -> None:
    """List entities.

    Examples:
        paperctl entities list
        paperctl entities list --type Host --output json
        paperctl entities list --name web-1
    """
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()

        with SWOClient(
            settings.api_token, api_url=settings.api_url, timeout=settings.timeout
        ) as client:
            entities = retry_with_backoff(
                lambda: client.list_entities(entity_type=entity_type, name=name)
            )

            if output == "text":
                text_formatter = TextFormatter(console)
                text_formatter.print_entities(entities)
            elif output == "json":
                json_formatter = JSONFormatter()
                console.print(json_formatter.format_entities(entities))
            elif output == "csv":
                csv_formatter = CSVFormatter()
                console.print(csv_formatter.format_entities(entities))
            else:
                console.print(f"[red]Invalid output format: {output}[/red]")
                raise typer.Exit(1) from None

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@entities_app.command("show")
def show_entity(
    entity_id: Annotated[str, typer.Argument(help="Entity ID")],
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output format: text|json|csv")
    ] = "text",
    api_token: Annotated[
        str | None, typer.Option("--token", envvar="SWO_API_TOKEN", help="API token")
    ] = None,
) -> None:
    """Show entity details.

    Examples:
        paperctl entities show e-abc123
        paperctl entities show e-abc123 --output json
    """
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()

        with SWOClient(
            settings.api_token, api_url=settings.api_url, timeout=settings.timeout
        ) as client:
            entity = retry_with_backoff(lambda: client.get_entity(entity_id))

            if output == "text":
                console.print(f"[bold]Entity {entity.id}[/bold]")
                console.print(f"Type: {entity.type}")
                console.print(f"Name: {entity.name}")
                console.print(f"Display Name: {entity.display_name or 'N/A'}")
                if entity.last_seen_time:
                    console.print(f"Last Seen: {entity.last_seen_time}")
                console.print(f"In Maintenance: {entity.in_maintenance}")
                if entity.tags:
                    console.print(f"Tags: {entity.tags}")
                if entity.attributes:
                    console.print(f"Attributes: {entity.attributes}")
            elif output == "json":
                json_formatter = JSONFormatter()
                console.print(json_formatter.format_any(entity))
            elif output == "csv":
                csv_formatter = CSVFormatter()
                console.print(csv_formatter.format_entities([entity]))
            else:
                console.print(f"[red]Invalid output format: {output}[/red]")
                raise typer.Exit(1) from None

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@entities_app.command("list-types")
def list_entity_types(
    api_token: Annotated[
        str | None, typer.Option("--token", envvar="SWO_API_TOKEN", help="API token")
    ] = None,
) -> None:
    """List available entity types.

    Examples:
        paperctl entities list-types
    """
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()

        with SWOClient(
            settings.api_token, api_url=settings.api_url, timeout=settings.timeout
        ) as client:
            types = retry_with_backoff(client.list_entity_types)

            for entity_type in types:
                console.print(entity_type)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None

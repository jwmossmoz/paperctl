"""Archives command implementation."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from paperctl.client import PapertrailClient
from paperctl.config import get_settings
from paperctl.formatters import CSVFormatter, JSONFormatter, TextFormatter
from paperctl.utils import retry_with_backoff

console = Console()

archives_app = typer.Typer(name="archives", help="Manage archives")


@archives_app.command("list")
def list_archives(
    output: Annotated[str, typer.Option("--output", "-o", help="Output format")] = "text",
    api_token: Annotated[
        str | None, typer.Option("--token", envvar="PAPERTRAIL_API_TOKEN", help="API token")
    ] = None,
) -> None:
    """List available archives.

    Examples:
        paperctl archives list
        paperctl archives list --output json
    """
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()

        with PapertrailClient(settings.api_token, timeout=settings.timeout) as client:
            archives = retry_with_backoff(client.list_archives)

            if output == "text":
                text_formatter = TextFormatter(console)
                text_formatter.print_archives(archives)
            elif output == "json":
                json_formatter = JSONFormatter()
                console.print(json_formatter.format_archives(archives))
            elif output == "csv":
                csv_formatter = CSVFormatter()
                console.print(csv_formatter.format_archives(archives))
            else:
                console.print(f"[red]Invalid output format: {output}[/red]")
                raise typer.Exit(1) from None

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@archives_app.command("download")
def download_archive(
    filename: Annotated[str, typer.Argument(help="Archive filename")],
    output_dir: Annotated[Path, typer.Option("--output-dir", "-d", help="Output directory")] = Path(
        "."
    ),
    api_token: Annotated[
        str | None, typer.Option("--token", envvar="PAPERTRAIL_API_TOKEN", help="API token")
    ] = None,
) -> None:
    """Download an archive file.

    Examples:
        paperctl archives download 2024-01-01.tsv.gz
        paperctl archives download 2024-01-01.tsv.gz --output-dir /tmp
    """
    try:
        settings = get_settings(api_token=api_token) if api_token else get_settings()

        with PapertrailClient(settings.api_token, timeout=settings.timeout) as client:
            console.print(f"Downloading {filename}...")
            content = retry_with_backoff(lambda: client.download_archive(filename))

            output_path = output_dir / filename
            output_path.write_bytes(content)

            console.print(f"[green]Downloaded {len(content)} bytes to {output_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None

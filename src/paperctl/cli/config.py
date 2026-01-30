"""Config command implementation."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from paperctl.config import get_config_paths, get_settings

console = Console()

config_app = typer.Typer(name="config", help="Manage configuration")

# Default config path
DEFAULT_CONFIG_PATH = Path.home() / ".paperctl.toml"


@config_app.command("show")
def show_config() -> None:
    """Show current configuration.

    Examples:
        paperctl config show
    """
    try:
        settings = get_settings()

        table = Table(title="Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("api_token", "***" if settings.api_token else "(not set)")
        table.add_row("timeout", str(settings.timeout))

        console.print(table)

        # Show config file paths
        console.print("\n[bold]Config file search paths:[/bold]")
        paths = get_config_paths()
        if paths:
            for path in paths:
                console.print(f"  [green]✓[/green] {path}")
        else:
            console.print("  [dim]No config files found[/dim]")

        console.print("\n[bold]Environment variables:[/bold]")
        console.print("  PAPERTRAIL_API_TOKEN")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@config_app.command("init")
def init_config(
    api_token: Annotated[
        str, typer.Option("--token", prompt=True, hide_input=True, help="Papertrail API token")
    ],
    timeout: Annotated[float, typer.Option("--timeout", help="API timeout in seconds")] = 30.0,
    config_path: Annotated[Path | None, typer.Option("--path", help="Config file path")] = None,
) -> None:
    """Initialize configuration file interactively.

    Examples:
        paperctl config init
        paperctl config init --path ./paperctl.toml
    """
    try:
        if config_path is None:
            config_path = DEFAULT_CONFIG_PATH

        config_content = f"""# Papertrail CLI Configuration
api_token = "{api_token}"
timeout = {timeout}
"""

        config_path.write_text(config_content)
        console.print(f"[green]Configuration saved to {config_path}[/green]")
        console.print("\n[yellow]Note: Keep your API token secure![/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None

"""Main CLI application with Typer."""

import typer
from rich.console import Console

from paperctl import __version__
from paperctl.cli.archives import archives_app
from paperctl.cli.config import config_app
from paperctl.cli.groups import groups_app
from paperctl.cli.pull import pull_command
from paperctl.cli.search import search_command, tail_command
from paperctl.cli.systems import systems_app

app = typer.Typer(
    name="paperctl",
    help="Modern CLI tool for querying Papertrail logs",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"paperctl version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """paperctl - Modern CLI tool for querying Papertrail logs."""
    pass


# Register commands
app.command("pull")(pull_command)
app.command("search")(search_command)
app.command("tail")(tail_command)

# Register subcommands
app.add_typer(systems_app)
app.add_typer(groups_app)
app.add_typer(archives_app)
app.add_typer(config_app)

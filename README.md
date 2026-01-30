# paperctl

[![PyPI](https://img.shields.io/pypi/v/paperctl.svg)](https://pypi.org/project/paperctl/)
[![Python Version](https://img.shields.io/pypi/pyversions/paperctl.svg)](https://pypi.org/project/paperctl/)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)
[![CI](https://github.com/jwmossmoz/paperctl/workflows/CI/badge.svg)](https://github.com/jwmossmoz/paperctl/actions)

A modern Python CLI tool for downloading logs from Papertrail. Built with Typer, httpx, and Pydantic.

## Installation

Using uv (recommended):

```bash
uv tool install paperctl
```

Or with pip:

```bash
pip install paperctl
```

From source:

```bash
git clone https://github.com/jwmossmoz/paperctl.git
cd paperctl
uv pip install -e .
```

## Quick Start

Set your Papertrail API token:

```bash
export PAPERTRAIL_API_TOKEN="your_token_here"
```

Pull logs from a system:

```bash
# Pull last hour of logs to stdout
paperctl pull web-1

# Save to file
paperctl pull web-1 --output logs.txt

# Pull specific time range
paperctl pull web-1 --since -24h --until -1h

# Search within logs
paperctl pull web-1 --query "error" --output errors.txt

# Export as JSON or CSV
paperctl pull web-1 --format json --output logs.json
paperctl pull web-1 --format csv --output logs.csv
```

## Features

- **Simple log downloading**: Target a system by name and pull logs locally
- **Flexible time parsing**: `-1h`, `-30m`, `1 day ago`, ISO timestamps
- **Multiple output formats**: text, JSON, CSV
- **Automatic pagination**: Handles large log volumes automatically
- **Progress indicators**: Visual feedback during downloads
- **Rate limit handling**: Automatic retry with backoff

## Commands

### pull

Download logs from a system.

```bash
paperctl pull <system> [OPTIONS]

Options:
  -o, --output PATH     Output file (default: stdout)
  --since TEXT          Start time (default: -1h)
  --until TEXT          End time (default: now)
  -f, --format TEXT     Output format: text|json|csv (default: text)
  -q, --query TEXT      Search query filter
```

### search

Advanced search across systems and groups.

```bash
paperctl search [QUERY] [OPTIONS]

Options:
  -s, --system TEXT     Filter by system name or ID
  -g, --group TEXT      Filter by group name or ID
  --since TEXT          Start time
  --until TEXT          End time
  -n, --limit INTEGER   Maximum events
  -o, --output TEXT     Output format
  -F, --file PATH       Write to file
```

### systems

Manage systems.

```bash
paperctl systems list              # List all systems
paperctl systems show <id>         # Show system details
```

### groups

Manage groups.

```bash
paperctl groups list               # List all groups
paperctl groups show <id>          # Show group with systems
```

### archives

Manage archives.

```bash
paperctl archives list                        # List available archives
paperctl archives download <filename>         # Download archive
```

### config

Manage configuration.

```bash
paperctl config show               # Show current config
paperctl config init               # Initialize config file
```

## Configuration

Configuration priority (highest to lowest):

1. CLI arguments
2. Environment variables (`PAPERTRAIL_*`)
3. Local config (`./paperctl.toml`)
4. Home config (`~/.paperctl.toml`)
5. XDG config (`~/.config/paperctl/config.toml`)

### Environment Variables

- `PAPERTRAIL_API_TOKEN` - Your Papertrail API token (required)

### Config File Format

Create `~/.paperctl.toml` with:

```toml
api_token = "your_token_here"
timeout = 30.0  # Optional: API timeout in seconds
```

## Time Parsing

paperctl supports multiple time formats:

- **Relative**: `-1h`, `-30m`, `-7d`, `1h`, `2d`
- **Natural language**: `1 hour ago`, `2 days ago`
- **ISO 8601**: `2024-01-01T00:00:00Z`
- **Special**: `now`

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run linters
uv run ruff check .
uv run mypy src

# Format code
uv run ruff format .

# Build package
uv build

# Install pre-commit hooks
uv run prek install
```

## License

Mozilla Public License 2.0 - see [LICENSE](LICENSE) for details.

## Links

- **GitHub**: https://github.com/jwmossmoz/paperctl
- **PyPI**: https://pypi.org/project/paperctl/
- **Papertrail API**: https://www.papertrail.com/help/http-api/

## Author

Jonathan Moss (jmoss@mozilla.com)

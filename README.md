# paperctl

[![PyPI](https://img.shields.io/pypi/v/paperctl.svg)](https://pypi.org/project/paperctl/)
[![Python Version](https://img.shields.io/pypi/pyversions/paperctl.svg)](https://pypi.org/project/paperctl/)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)
[![CI](https://github.com/jwmossmoz/paperctl/workflows/CI/badge.svg)](https://github.com/jwmossmoz/paperctl/actions)

Download logs from Papertrail. Built with Typer, httpx, and Pydantic.

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

Pull logs from a single system:

```bash
paperctl pull web-1                    # Last hour to stdout
paperctl pull web-1 --output logs.txt  # Save to file
paperctl pull web-1 --since -24h       # Custom time range
```

Pull from multiple systems in parallel:

```bash
# Download from three systems at once
paperctl pull web-1,web-2,web-3 --output logs/

# Search across multiple systems
paperctl pull web-1,web-2,db-1 --query "error" --output errors/

# Works with any combination
paperctl pull prod-*,staging-* --since -1h --output recent/
```

When you specify multiple systems, paperctl downloads them in parallel with automatic rate limiting (Papertrail allows 25 requests per 5 seconds). Each system gets its own file in the output directory.

## What It Does

- Downloads logs from one or more Papertrail systems
- Handles pagination automatically (no manual limit setting)
- Respects API rate limits (25 requests per 5 seconds)
- Runs parallel downloads when pulling from multiple systems
- Parses relative times like `-1h` or `2 days ago`
- Outputs as text, JSON, or CSV

## Commands

### pull

Download logs from systems.

```bash
paperctl pull <system>[,<system>...] [OPTIONS]

Arguments:
  <system>              System name(s) or ID(s), comma-separated

Options:
  -o, --output PATH     Output file (single system) or directory (multiple)
  --since TEXT          Start time (default: -1h)
  --until TEXT          End time (default: now)
  -f, --format TEXT     Output format: text|json|csv (default: text)
  -q, --query TEXT      Search query filter
```

**Examples:**

```bash
# Single system
paperctl pull web-1
paperctl pull web-1 --output logs.txt
paperctl pull web-1 --query "error" --since -24h

# Multiple systems (parallel)
paperctl pull web-1,web-2,web-3 --output logs/
paperctl pull prod-api,prod-worker --query "500" --output errors/
```

### search

Search logs with filters.

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

List systems or show details.

```bash
paperctl systems list              # List all systems
paperctl systems show <id>         # Show system details
```

### groups

List groups or show details.

```bash
paperctl groups list               # List all groups
paperctl groups show <id>          # Show group with systems
```

### archives

Download historical archives.

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

Configuration is loaded from (highest priority first):

1. CLI arguments
2. Environment variable: `PAPERTRAIL_API_TOKEN`
3. Local config: `./paperctl.toml`
4. Home config: `~/.paperctl.toml`
5. XDG config: `~/.config/paperctl/config.toml`

Create `~/.paperctl.toml`:

```toml
api_token = "your_token_here"
timeout = 30.0  # Optional: API timeout in seconds
```

## Time Formats

Relative times:
- `-1h`, `-30m`, `-7d` (ago)
- `1h`, `2d` (future)

Natural language:
- `1 hour ago`, `2 days ago`

ISO 8601:
- `2024-01-01T00:00:00Z`

Special:
- `now`

## Rate Limiting

Papertrail's API allows 25 requests per 5 seconds. When pulling from multiple systems, paperctl automatically:
- Runs downloads in parallel
- Tracks requests across all systems
- Throttles to stay under the limit
- Retries with backoff on 429 errors

You don't need to worry about rate limits or pagination. Just specify what you want and paperctl handles the rest.

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

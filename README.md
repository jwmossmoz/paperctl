# paperctl

A modern Python CLI tool for querying Papertrail logs. Built with Typer, httpx, and Pydantic.

## Features

- **Search logs** with flexible time parsing (`-1h`, `2024-01-01T00:00:00Z`, `1 hour ago`)
- **Filter by system or group** by name or ID
- **Multiple output formats** (text, JSON, CSV)
- **Automatic pagination** through large result sets
- **Rate limit handling** with automatic retry and backoff
- **Configuration file support** with environment variable overrides
- **Type-safe** with full type hints and Pydantic models

## Installation

```bash
pip install paperctl
```

Or install from source:

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

Or create a config file:

```bash
paperctl config init
```

Search logs:

```bash
# Search for errors in the last hour
paperctl search "error" --since -1h

# Search specific system with JSON output
paperctl search --system web-1 --output json

# Search with time range
paperctl search "status=500" --since "2024-01-01T00:00:00Z" --until now

# Write results to file
paperctl search "error" --since -1h --output csv --file errors.csv
```

## Commands

### search

Search Papertrail logs with flexible filtering and time ranges.

```bash
paperctl search [QUERY] [OPTIONS]

Options:
  -s, --system TEXT        Filter by system name or ID
  -g, --group TEXT         Filter by group name or ID
  --since TEXT            Start time (-1h, 2024-01-01T00:00:00Z, "1 hour ago")
  --until TEXT            End time (now, -30m, ISO timestamp)
  -n, --limit INTEGER     Maximum events (default: 1000)
  -f, --follow            Tail mode (continuous streaming)
  -o, --output TEXT       Output format: text|json|csv (default: text)
  -F, --file PATH         Write output to file
```

### tail

Tail logs in real-time (alias for `search --follow`).

```bash
paperctl tail [QUERY] [OPTIONS]
```

### systems

List and show system details.

```bash
# List all systems
paperctl systems list

# Show system details
paperctl systems show 12345

# Output as JSON
paperctl systems list --output json
```

### groups

List and show group details with associated systems.

```bash
# List all groups
paperctl groups list

# Show group with systems
paperctl groups show 12345
```

### archives

List and download archive files.

```bash
# List available archives
paperctl archives list

# Download archive
paperctl archives download 2024-01-01.tsv.gz

# Download to specific directory
paperctl archives download 2024-01-01.tsv.gz --output-dir /tmp
```

### config

Manage configuration.

```bash
# Show current config
paperctl config show

# Initialize config file
paperctl config init
```

## Configuration

Configuration priority (highest to lowest):

1. CLI arguments
2. Environment variables (`PAPERTRAIL_*`)
3. Local config (`./paperctl.toml`)
4. Home config (`~/.paperctl.toml`)
5. XDG config (`~/.config/paperctl/config.toml`)

### Environment Variables

- `PAPERTRAIL_API_TOKEN` - API token (required)
- `PAPERTRAIL_DEFAULT_LIMIT` - Default event limit
- `PAPERTRAIL_DEFAULT_OUTPUT` - Default output format
- `PAPERTRAIL_TIMEOUT` - API request timeout

### Config File Format

```toml
api_token = "your_token_here"
default_output = "text"
default_limit = 1000
timeout = 30.0
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
make test

# Run linters
make lint

# Format code
make format

# Build package
make build
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=paperctl --cov-report=html
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- **GitHub**: https://github.com/jwmossmoz/paperctl
- **PyPI**: https://pypi.org/project/paperctl/
- **Papertrail API**: https://help.papertrailapp.com/kb/how-it-works/http-api/

## Author

Jonathan Moss (jmoss@mozilla.com)

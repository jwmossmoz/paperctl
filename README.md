# paperctl

[![PyPI](https://img.shields.io/pypi/v/paperctl.svg)](https://pypi.org/project/paperctl/)
[![Python Version](https://img.shields.io/pypi/pyversions/paperctl.svg)](https://pypi.org/project/paperctl/)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)
[![CI](https://github.com/jwmossmoz/paperctl/workflows/CI/badge.svg)](https://github.com/jwmossmoz/paperctl/actions)

Download logs from SolarWinds Observability. Built with Typer, httpx, and Pydantic.

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

`paperctl` 2.x talks to the SolarWinds Observability logs API.

Set your API token:

```bash
export SWO_API_TOKEN="your_token_here"
```

For easier upgrades from 1.x, `PAPERTRAIL_API_TOKEN` is also accepted as a legacy
environment-variable alias. The token itself still needs to be valid for the SWO API.

Pull logs from a single host:

```bash
paperctl pull web-1
paperctl pull web-1 --output logs.txt
paperctl pull web-1 --since -24h
```

Search logs across all hosts or a specific host:

```bash
paperctl search "error AND timeout" --since -1h
paperctl search --system web-1 "startup finished" --since -24h
```

List available hosts via the entities API:

```bash
paperctl entities list --type Host
paperctl entities list --name web-1 --output json
```

## What It Does

- Queries SolarWinds Observability logs with automatic pagination
- Pulls logs from one or more hosts, with parallel downloads for multi-host pulls
- Resolves partial hostnames such as Taskcluster VM IDs
- Parses relative times like `-1h` and ISO timestamps
- Outputs as text, JSON, or CSV

## Migration From 1.x

Version 2.x is a breaking change:

- Auth header changed from `X-Papertrail-Token` to `Authorization: Bearer`
- API base URL changed from `papertrailapp.com` to SolarWinds Observability
- `systems`/`groups`/`archives` commands were replaced by `entities`
- `PAPERTRAIL_API_TOKEN` is only a legacy env-var alias now; the token itself must be valid for SWO

## Commands

### pull

Download logs from one or more hosts.

```bash
paperctl pull <system>[,<system>...] [OPTIONS]

Arguments:
  <system>              System name(s), comma-separated

Options:
  -o, --output PATH     Output file (single system) or directory (multiple)
  --since TEXT          Start time (default: all logs)
  --until TEXT          End time (default: now)
  -f, --format TEXT     Output format: text|json|csv (default: text)
  -q, --query TEXT      Search query filter
```

Examples:

```bash
paperctl pull web-1
paperctl pull vm-abc123 --since -24h
paperctl pull web-1,web-2 --output logs/
```

### search

Search logs with optional host filtering.

```bash
paperctl search [QUERY] [OPTIONS]

Options:
  -s, --system TEXT     Filter by system name
  --since TEXT          Start time
  --until TEXT          End time
  -n, --limit INTEGER   Maximum events
  -o, --output TEXT     Output format
  -F, --file PATH       Write output to file
```

### tail

Tail logs. This is currently an alias for `search --follow`.

### entities

List and inspect entities such as hosts.

```bash
paperctl entities list
paperctl entities list --type Host --output json
paperctl entities show <entity-id>
paperctl entities list-types
```

### config

Manage configuration.

```bash
paperctl config show
paperctl config init
```

## Configuration

Configuration is loaded from highest to lowest priority:

1. CLI arguments
2. `SWO_API_TOKEN`
3. `PAPERTRAIL_API_TOKEN` as a legacy alias
4. Local config: `./paperctl.toml`
5. Home config: `~/.paperctl.toml`
6. XDG config: `~/.config/paperctl/config.toml`

Create `~/.paperctl.toml`:

```toml
api_token = "your_token_here"
api_url = "https://api.na-01.cloud.solarwinds.com"
timeout = 30.0
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
- **SolarWinds Observability**: https://documentation.solarwinds.com/en/success_center/observability/default.htm

## Author

Jonathan Moss (jmoss@mozilla.com)

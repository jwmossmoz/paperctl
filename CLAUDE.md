# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**paperctl** is a modern Python CLI tool for downloading logs from Papertrail. It handles pagination automatically, respects API rate limits (25 req/5s), and supports parallel downloads from multiple systems.

Built with: Typer (CLI), httpx (HTTP), Pydantic (models/config), Rich (terminal output), python-dateutil (time parsing)

## Development Commands

```bash
# Setup
uv sync --all-groups              # Install all dependencies
uv run prek install               # Install pre-commit hooks (prek, not pre-commit)

# Testing
uv run pytest                     # Run all tests
uv run pytest tests/test_client.py::test_search  # Run single test
uv run pytest -v                  # Verbose output
uv run pytest --cov-report=html   # Generate HTML coverage report

# Linting & Type Checking
uv run ruff check .               # Lint (includes isort, pyupgrade, etc.)
uv run ruff format .              # Format code
uv run mypy src                   # Type checking (strict mode enabled)

# Build
uv build                          # Build wheel and sdist

# Run CLI during development
uv run paperctl --help
uv run paperctl pull web-1 --output test.txt
```

## Architecture

### Core Components

**Client Layer** (`src/paperctl/client/`):
- `api.py` - Sync `PapertrailClient` with automatic pagination via `search_iter()`
- `async_api.py` - Async `AsyncPapertrailClient` for parallel requests
- `models.py` - Pydantic models: `Event`, `System`, `Group`, `Archive`, `SearchResponse`
- `exceptions.py` - Custom exceptions: `APIError`, `RateLimitError`, `AuthenticationError`

**CLI Layer** (`src/paperctl/cli/`):
- `main.py` - Typer app, registers subcommands
- `pull.py` - Main command: detects single vs multi-system by comma, uses sync or async client
- `search.py` - Search logs with filters, supports tail mode
- `systems.py`, `groups.py`, `archives.py`, `config.py` - Other subcommands

**Utils** (`src/paperctl/utils/`):
- `rate_limiter.py` - Token bucket rate limiter for parallel downloads (25 req/5s)
- `retry.py` - Exponential backoff retry wrapper for 429 rate limit errors
- `time.py` - Parse relative times (`-1h`, `2 days ago`) and ISO timestamps

**Config** (`src/paperctl/config/`):
- `settings.py` - Pydantic settings with env var support (`PAPERTRAIL_API_TOKEN`)
- Priority: CLI args → env vars → local config → home config → XDG config

**Formatters** (`src/paperctl/formatters/`):
- `text.py` - Rich tables for terminal output
- `json.py` - JSON serialization
- `csv.py` - CSV output

### Key Design Patterns

**Automatic Pagination**: Both sync and async clients use `search_iter()` to automatically handle Papertrail's `min_id` pagination. Users never think about limits or page tokens.

**Parallel vs Serial**: The `pull` command detects comma-separated systems and switches between:
- Single system: Uses sync `PapertrailClient` with progress spinner
- Multiple systems: Uses async `AsyncPapertrailClient` with per-system progress, shared `RateLimiter`

**Rate Limiting**: Papertrail API limit is 25 requests per 5 seconds. The token bucket rate limiter (`RateLimiter`) tracks requests across all parallel downloads and throttles to stay within limits.

**Query Syntax Limitation**: Papertrail search does **not** support regex or wildcards. Only text matching with boolean operators (AND/OR/NOT). This is documented in all `--query` help text.

**Default Output Location**: When no `--output` specified, logs write to `~/.cache/paperctl/logs/<system>.<ext>` for persistence.

## Release Process

Version must be updated in **three places**:
1. `pyproject.toml` - `version = "X.Y.Z"`
2. `src/paperctl/__init__.py` - `__version__ = "X.Y.Z"`
3. `CHANGELOG.md` - Add release section with date

Then:
```bash
uv sync --all-groups              # Update lockfile
git add pyproject.toml src/paperctl/__init__.py CHANGELOG.md uv.lock
git commit -m "Release vX.Y.Z"
git tag vX.Y.Z
git push && git push --tags
```

GitHub Actions automatically publishes to PyPI via trusted publishing (OIDC).

**Important**: PyPI license classifier must be `"License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)"` with a **space**, not `(MPL-2.0)` with a hyphen.

## Testing Notes

- Use `pytest-httpx` for mocking HTTP requests
- Tests live in `tests/` with corresponding structure to `src/paperctl/`
- Coverage requirement: tests run with `--cov=paperctl` (configured in pyproject.toml)
- Mock the Papertrail API responses, don't make real requests

## Configuration Files

- `pyproject.toml` - Project metadata, dependencies, tool config (ruff, mypy, pytest)
- `.pre-commit-config.yaml` - Hooks for prek (ruff, detect-secrets, shellcheck, actionlint, zizmor)
- `.github/workflows/ci.yml` - Linting and testing on push/PR
- `.github/workflows/release.yml` - Build and publish to PyPI on tags

## Common Pitfalls

1. **Don't add `uv pip install`** - Use `uv sync` or `uv add/remove` instead
2. **Don't manually edit dependencies in pyproject.toml** - Use `uv add <pkg>` or `uv remove <pkg>`
3. **Pre-commit hooks use prek, not pre-commit** - This is a Rust-native faster alternative
4. **Search queries don't support regex** - Users sometimes ask for wildcards like `*vmprod*`, but Papertrail only supports text matching
5. **Rate limiting is per-account, not per-request** - The 25 req/5s limit applies globally across parallel downloads

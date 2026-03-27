# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.1] - 2026-03-27

### Fixed
- Accept `PAPERTRAIL_API_TOKEN` as a legacy environment-variable alias in 2.x
- Clarify authentication errors when a token is not valid for the SolarWinds Observability API
- Update README and config messaging to match the actual 2.x CLI and migration path

## [2.0.0] - 2026-02-20

### Changed
- **Breaking**: Migrated from Papertrail API to SolarWinds Observability API
- Auth header changed from `X-Papertrail-Token` to `Authorization: Bearer`
- Environment variable changed from `PAPERTRAIL_API_TOKEN` to `SWO_API_TOKEN`
- API base URL changed to `https://api.na-01.cloud.solarwinds.com`
- Client renamed from `PapertrailClient` to `SWOClient` (sync and async)
- Exception base class renamed from `PapertrailError` to `SWOError`
- Pagination changed from `min_id`/`max_id` to URL-based cursor pagination
- `search()`/`search_iter()` renamed to `get_logs()`/`logs_iter()`
- `list_systems()` replaced by `list_entities(entity_type="Host")`
- Event model fields changed: `source_name` -> `hostname`, `received_at` -> `time`, removed `id`/`source_id`/`source_ip`/`facility`/`display_received_at`
- Systems replaced by entities with string IDs and richer metadata

### Added
- `api_url` configuration field for different SWO regions
- `entities` CLI subcommand with `list`, `show`, and `list-types` commands
- Entity model with tags, attributes, and maintenance status
- `--api-url` option in `config init`

### Removed
- `groups` CLI subcommand and Group model (not in SWO API)
- `archives` CLI subcommand and Archive model (not in SWO API)
- `systems` CLI subcommand (replaced by `entities`)
- `--group` option from search/tail commands
- `_request_raw()` method and `download_archive()` method

## [1.2.0] - 2026-01-29

### Added
- Partial/fuzzy matching for system names in `pull` command - use Taskcluster worker IDs like `vm-abc123` to match `vm-abc123.reddog.microsoft.com`
- Downloads all available logs by default (no `--since` required)

### Changed
- Default `--since` for `pull` changed from `-1h` to no limit (all logs)

## [1.1.1] - 2026-01-29

### Fixed
- Event `facility` and `severity` fields now accept null values from API

## [1.1.0] - 2026-01-29

### Added
- Async retry with exponential backoff for transient failures
- `total_limit` parameter to `search_iter()` for capping total events returned
- Sync `RateLimiter` class for single-threaded use

### Changed
- Rate limiting now applied per HTTP request instead of per event (fixes rate limit calculation)
- Streaming output for pull and search commands (reduces memory usage for large downloads)
- **Breaking**: `search_iter()` parameter `limit` renamed to `page_limit`; use `total_limit` for overall cap

### Fixed
- Rate limiter race condition in async code (now re-checks after sleep)

## [1.0.1] - 2026-01-30

### Added
- Parallel multi-system pull: download from multiple systems at once with `paperctl pull web-1,web-2,web-3`
- Automatic rate limiting across parallel downloads (25 requests per 5 seconds)
- Token bucket rate limiter for staying within API limits

### Changed
- Default output location is now `~/.cache/paperctl/logs/<system>.txt` for persistent storage
- Each system gets its own file when pulling from multiple systems

## [1.0.0] - 2026-01-30

### Added
- Initial release of paperctl CLI tool
- `pull` command for downloading logs from a single system
- `search` command with flexible time parsing (`-1h`, ISO timestamps, natural language)
- Systems, groups, and archives management commands
- Configuration management with file and environment variable support
- Multiple output formats: text (with Rich tables), JSON, CSV
- Automatic pagination through large result sets
- Rate limit handling with retry and exponential backoff
- Progress indicators during downloads
- Full type hints with Pydantic models
- Comprehensive test coverage

[Unreleased]: https://github.com/jwmossmoz/paperctl/compare/v2.0.1...HEAD
[2.0.1]: https://github.com/jwmossmoz/paperctl/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/jwmossmoz/paperctl/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/jwmossmoz/paperctl/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/jwmossmoz/paperctl/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/jwmossmoz/paperctl/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/jwmossmoz/paperctl/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/jwmossmoz/paperctl/releases/tag/v1.0.0

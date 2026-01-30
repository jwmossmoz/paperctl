# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/jwmossmoz/paperctl/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/jwmossmoz/paperctl/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/jwmossmoz/paperctl/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/jwmossmoz/paperctl/releases/tag/v1.0.0

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial implementation of paperctl CLI tool
- Search command with flexible time parsing (`-1h`, ISO timestamps, natural language)
- Systems, groups, and archives management commands
- Configuration management with file and environment variable support
- Multiple output formats: text (with Rich tables), JSON, CSV
- Automatic pagination through large result sets
- Rate limit handling with retry and exponential backoff
- Full type hints with Pydantic models
- Comprehensive test coverage

[Unreleased]: https://github.com/jwmossmoz/paperctl/compare/v0.1.0...HEAD

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-05-19

### Changed

- Document published `uvx garmin-connect-mcp` usage as the primary setup path
- Simplify Claude Desktop configuration for published `uvx` usage
- Store interactive setup credentials in `~/.garminconnect.env` by default

## [1.0.0] - 2026-05-19

### Added

- Initial Garmin Connect MCP server release
- Garmin Connect activity, health, training, profile, device, gear, weight, workout, and women's health tools
- MCP resources for athlete profile, training readiness, and daily health context
- MCP prompts for training analysis, sleep quality, readiness checks, activity analysis, run comparison, and health summaries
- `garmin-connect-mcp` server entrypoint
- `garmin-connect-mcp auth` interactive authentication setup with MFA token persistence
- Docker image support via GitHub Container Registry

[1.0.1]: https://github.com/eddmann/garmin-connect-mcp/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/eddmann/garmin-connect-mcp/releases/tag/v1.0.0

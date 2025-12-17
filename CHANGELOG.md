# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2025-12-17

### Changed
- **Cleanup**: Removed backward compatibility files (setup.py, requirements.txt)
- **Organization**: Moved all documentation to `docs/` folder
- **Simplified**: Single installation method using uv with virtual environments
- **Streamlined**: Removed redundant scripts and tools

### Removed
- setup.py (replaced by pyproject.toml)
- requirements.txt (redundant)
- Legacy installation scripts
- Development utilities

## [1.0.1] - 2025-12-17

### Changed
- **Package Management**: Migrated to `uv` for 10-100x faster installation
- Added `pyproject.toml` (modern Python packaging standard)
- Updated installation scripts to use uv

### Added
- Development dependencies in `[project.optional-dependencies]`
- Tool configurations (black, ruff, mypy) in `pyproject.toml`
- Comprehensive documentation

## [1.0.0] - 2025-12-17

### Added
- Initial release of COS CLI
- Interactive configuration with `cos configure`
- List buckets and objects with `cos ls`
- Upload files with `cos cp` (local to COS)
- Download files with `cos cp` (COS to local)
- Copy objects with `cos cp` (COS to COS)
- Delete objects with `cos rm`
- Create buckets with `cos mb`
- Remove buckets with `cos rb`
- Support for multiple profiles
- Support for STS temporary credentials
- Support for role assumption
- Rich progress bars for file transfers
- Multiple output formats (json, table, text)
- Recursive operations for directories
- Environment variable support
- SSL verification options
- Debug mode for troubleshooting

### Features
- AWS CLI-like command structure
- Secure credential management
- Configuration file support
- Multiple region support
- Error handling with helpful messages
- Colorized output with Rich library

### Security
- Credentials stored with 600 permissions
- Support for STS temporary credentials
- Token caching and automatic refresh
- Never logs sensitive information

## [Unreleased]

### Planned
- `cos sync` command for directory synchronization
- `cos mv` command for moving objects
- `cos presign` command for generating presigned URLs
- Multipart upload for large files
- Parallel file transfers
- Resume capability for interrupted transfers
- Include/exclude pattern matching
- Lifecycle management commands
- Bucket policy management
- CORS configuration
- Versioning support
- Bandwidth throttling
- Cross-region replication

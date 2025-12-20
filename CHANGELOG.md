# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-20

### Added - Major Feature Release

#### Advanced Bucket Management Commands
- **`cos lifecycle` command group**: Manage bucket lifecycle policies
  - `cos lifecycle get cos://bucket` - Retrieve lifecycle configuration
  - `cos lifecycle put cos://bucket --config lifecycle.json` - Set lifecycle rules
  - `cos lifecycle delete cos://bucket` - Remove lifecycle configuration
  - Support for transition and expiration rules

- **`cos policy` command group**: Manage bucket access policies
  - `cos policy get cos://bucket` - Get bucket policy
  - `cos policy put cos://bucket --policy policy.json` - Set access policy
  - `cos policy delete cos://bucket` - Remove bucket policy
  - Full IAM policy support

- **`cos cors` command group**: Configure Cross-Origin Resource Sharing
  - `cos cors get cos://bucket` - View CORS configuration
  - `cos cors put cos://bucket --config cors.json` - Set CORS rules
  - `cos cors delete cos://bucket` - Remove CORS configuration
  - Configure allowed origins, methods, and headers

- **`cos versioning` command group**: Manage object versioning
  - `cos versioning get cos://bucket` - Check versioning status
  - `cos versioning enable cos://bucket` - Enable versioning
  - `cos versioning suspend cos://bucket` - Suspend versioning
  - Protect against accidental deletions

#### Enhanced Transfer Features
- **Pattern Matching**: Include/exclude files in cp and sync commands
  - `--include "*.txt"` - Include only matching files
  - `--exclude "test_*"` - Exclude matching files
  - Multiple patterns supported: `--include "*.py" --include "*.md"`
  - Glob pattern support with fnmatch

- **Checksum Verification**: MD5-based integrity checking
  - `cos sync --checksum` - Use MD5 checksums for comparison
  - Automatic multipart upload detection
  - Compare local and remote file integrity
  - Skip identical files even if timestamps differ

- **Bandwidth Throttling**: Control transfer speeds
  - `BandwidthThrottle` class for rate limiting
  - Configurable max bytes per second
  - Real-time speed monitoring
  - Prevents network saturation

- **Resume Capability**: Continue interrupted transfers
  - `ResumeTracker` class for progress tracking
  - Cache transfer state to disk
  - Automatic resume on retry
  - Clean up completed transfers

#### Utility Enhancements
- Pattern matching utilities (`matches_pattern`, `should_process_file`)
- Checksum computation (`compute_file_checksum` for MD5, SHA1, SHA256)
- Checksum comparison (`compare_checksums` with ETag validation)
- Bandwidth monitoring and throttling
- Transfer progress tracking and caching

### Enhanced
- **cp command**: Now supports --include and --exclude patterns
  - `cos cp ./src/ cos://bucket/ -r --include "*.py" --exclude "test_*"`
  - Filters applied to uploads, downloads, and copies
  - Works with recursive operations

- **sync command**: Enhanced with checksums and patterns
  - `cos sync ./local/ cos://bucket/ --checksum` - Verify integrity
  - `cos sync ./src/ cos://bucket/ --include "*.js"` - Filter files
  - More accurate sync with MD5 comparison
  - Pattern-based selective synchronization

- **COSClient**: Added 12 new methods for advanced operations
  - Lifecycle: get_bucket_lifecycle, put_bucket_lifecycle, delete_bucket_lifecycle
  - Policy: get_bucket_policy, put_bucket_policy, delete_bucket_policy
  - CORS: get_bucket_cors, put_bucket_cors, delete_bucket_cors
  - Versioning: get_bucket_versioning, put_bucket_versioning

### Testing
- **42 new tests** for advanced features and utilities
  - 16 tests for lifecycle, policy, CORS, versioning commands
  - 26 tests for pattern matching, throttling, checksums
  - **Total: 169 tests**, all passing (100%)

### Documentation
- Updated README with all new commands and examples
- Enhanced QUICK_REFERENCE with advanced usage patterns
- Updated COS_CLI_DEVELOPMENT_PLAN with V2.0 completion status
- Added comprehensive inline documentation for all new functions
- Example configuration files for lifecycle, policy, and CORS

### Breaking Changes
None - All v1.x features remain fully compatible

## [1.1.0] - 2025-12-18

### Added
- **`cos mv` command**: Move or rename objects within and between buckets
  - Single object rename: `cos mv cos://bucket/old.txt cos://bucket/new.txt`
  - Directory move: `cos mv cos://bucket/old/ cos://bucket/new/ --recursive`
  - Cross-bucket move: `cos mv cos://bucket1/file cos://bucket2/file`
  - Confirmation prompt before overwriting existing objects

- **`cos presign` command**: Generate presigned URLs for temporary access
  - Default 1-hour expiration, configurable from 60 seconds to 7 days
  - Support for GET (download), PUT (upload), and DELETE operations
  - Usage examples included in output: `cos presign cos://bucket/file.txt --expires-in 7200`

- **`cos sync` command**: Bidirectional directory synchronization
  - Sync local to COS: `cos sync ./local/ cos://bucket/remote/`
  - Sync COS to local: `cos sync cos://bucket/remote/ ./local/`
  - `--delete` flag: Remove files not in source (exact mirror)
  - `--dryrun` flag: Preview changes without execution
  - `--size-only` flag: Fast comparison by file size only
  - Smart comparison by size and modification time

### Changed
- Updated documentation with examples for new commands
- Enhanced README with mv, sync, and presign usage
- Updated QUICK_REFERENCE with comprehensive examples
- Marked Phase 2 features as completed in development plan

### Documentation
- Added presigned URL examples to README
- Added sync operation patterns to QUICK_REFERENCE
- Updated command reference table with all 10 commands

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

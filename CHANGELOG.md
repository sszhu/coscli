# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.1] - 2026-01-14

### Added
- Transfer Tuning across commands:
  - `--part-size` for multipart uploads and ranged downloads (human-friendly sizes)
  - `--max-retries`, `--retry-backoff`, `--retry-backoff-max` for robust retry with exponential backoff
  - Resumable ranged downloads for `cp` and `sync` (opt-out via `--no-resume`)
  - `mv` (local→COS) now supports multipart with streaming progress when enabled
- Documentation:
  - New Transfer Tuning cheat sheet in README
  - Examples for tuning in cp/mv/sync sections

### Fixed
- Prevent truncated downloads by fully consuming each HTTP range and advancing offsets by actual bytes read
- Clear error when object does not exist before download (HEAD/List/range 0–0 fallback)

### Changed
- `sync` retains simple SDK paths under `--no-progress` to preserve script expectations; uses advanced streaming only when progress is enabled

## [2.2.0] - 2025-12-22

### Added
- **Prefix-Restricted STS Tokens**: Comprehensive policy-based access control
  - New `--bucket` option: Scope credentials to specific bucket
  - New `--prefix` option: Restrict access to specific path/folder
  - New `--region` option: Override default region (now ap-shanghai)
  - New `--appid` option: Manually specify APPID
  - New `--action` option: Specify custom CAM actions (repeatable)
  - New `--read-only` flag: Quick mode for read-only access
- **Policy Building**: Automatic CAM policy generation for scoped access
  - `build_policy()` function: Constructs resource-restricted policies
  - Support for prefix-based wildcards (`prefix/*`)
  - Bucket-level operations (ListMultipartUploads, ListParts)
- **APPID Extraction**: Automatic extraction from bucket names
  - `extract_appid_from_bucket()` validates 10-digit APPID format
- **Bucket Validation**: `validate_bucket_name()` with Tencent COS rules
- **Comprehensive Test Suite**: 26 tests for token functionality (100% passing)
  - Policy building tests (6)
  - APPID extraction tests (5)
  - CLI integration tests (11)
  - STS manager tests (4)
- **Documentation Updates**:
  - [STS_PREFIX_ACCESS_GUIDE.md](docs/STS_PREFIX_ACCESS_GUIDE.md) - Complete guide with examples
  - [TOKEN_USAGE_GUIDE.md](docs/TOKEN_USAGE_GUIDE.md) - Token management patterns
  - [CREDENTIAL_PRECEDENCE.md](docs/CREDENTIAL_PRECEDENCE.md) - **NEW**: Complete credential resolution rules
  - [SECURITY_REVIEW.md](SECURITY_REVIEW.md) - Security audit and sanitization

### Changed
- **Default Region**: Changed from ap-singapore to ap-shanghai globally
- **STSTokenManager**: Enhanced to support policy-based credentials
  - Disables caching when policy provided (ensures fresh scoped tokens)
  - Accepts both policy dict and policy string
- **Token Output**: Fixed Click echo issues (removed unsupported `end` parameter)
- **Credential Resolution**: **MAJOR REFACTOR** - Clear precedence rules
  - `get_credentials()`: Explicit mode detection prevents conflicts
  - Environment `COS_TOKEN` now completely isolates from config file
  - Added `_source` field to track credential origin
  - Validation ensures temporary credentials are complete
  - See [CREDENTIAL_PRECEDENCE.md](docs/CREDENTIAL_PRECEDENCE.md) for full details

### Fixed
- **Credential Conflicts**: Environment temporary tokens no longer conflict with config `assume_role`
  - When `COS_TOKEN` is set, config file is completely bypassed
  - Prevents mixed credential sources causing ambiguous behavior
  - Clear error messages when temporary credentials are incomplete
- **GetBucket Permission**: Listing now works with prefix-restricted tokens
  - Removed restrictive prefix condition on GetBucket action
  - Object access still properly restricted to specified prefix
  - Policy allows listing entire bucket but only accessing objects within prefix
  - See [STS_PREFIX_ACCESS_GUIDE.md](docs/STS_PREFIX_ACCESS_GUIDE.md#troubleshooting) for details

### Security
- **Sanitized Documentation**: Removed all production bucket names and real account identifiers
- **Generic Examples**: All docs now use placeholder values (my-bucket-1234567890, etc.)

## [2.0.1] - 2025-12-21

### Added
- **PyPI Package**: Now published on PyPI as `tencent-cos-cli`
- Installation via pip: `pip install tencent-cos-cli`
- Comprehensive release documentation for first public release
- [Token Usage Guide](docs/TOKEN_USAGE_GUIDE.md) with CI/CD examples
- [PyPI Upload Guide](PYPI_UPLOAD_GUIDE.md) for maintainers

### Fixed
- **cp command**: Fixed destination handling for paths with trailing slash
  - Files uploaded to `cos://bucket/path/` now correctly create `path/filename`
  - Previously would create directory object instead of file
- **Help formatting**: Fixed indentation in all command help texts
  - All examples now display with proper 2-space indentation
  - Line breaks preserved correctly using Click's `\b` marker
- **token command**: Fixed environment variable output for sourcing
  - Info messages now go to stderr when `--output env`
  - Clean stdout allows: `cos token --output env > creds.sh && source creds.sh`

### Enhanced
- Data backup/restore script with Tencent COS support
- Multi-provider backup (AWS S3 + Tencent COS)
- SSL bypass helper for corporate network uploads
- Improved error messages and user feedback
- Documentation organization and completeness

### Documentation
- Added pip installation as recommended method in README
- Created comprehensive release notes for v2.0.1
- Updated all documentation with PyPI installation instructions
- Added contributing guidelines

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

# Tencent COS CLI

A powerful command-line interface for Tencent Cloud Object Storage (COS), designed with a similar experience to AWS CLI.

## Features

- 🚀 **Easy to Use**: Intuitive commands similar to AWS CLI
- 🔐 **Secure**: Support for STS temporary credentials and role assumption
- ⚡ **Fast**: Multipart uploads and parallel transfers
- 🎨 **Beautiful**: Rich progress bars and formatted output
- 🔧 **Flexible**: Multiple profiles, regions, and output formats
- 📦 **Complete**: Upload, download, sync, and manage buckets

## Installation

### Quick Install (with new venv)
```bash
./install.sh
```

This will:
1. Install `uv` (if not present)
2. Create a virtual environment
3. Install COS CLI and dependencies

Then activate:
```bash
source .venv/bin/activate
```

### Install in Current Environment
If you're already in a conda environment or existing venv:
```bash
./install.sh --current
```

This installs COS CLI in your current Python environment without creating a new venv

### Manual Installation
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv and install
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Requirements
- Python 3.8+
- uv package manager
- Tencent Cloud Account with COS access

### Troubleshooting Installation

If you encounter SSL certificate errors during installation (common in corporate networks):

```bash
# The install.sh script handles this automatically, but if needed:
curl -LsSfk https://astral.sh/uv/install.sh | sh
```

**SSL Certificate Issues?**
```bash
# Run diagnostic tool to identify the issue
python diagnose_ssl.py
```

**📖 More details**: 
- [docs/UV_GUIDE.md](docs/UV_GUIDE.md)
- [docs/SSL_TROUBLESHOOTING.md](docs/SSL_TROUBLESHOOTING.md) - Comprehensive SSL troubleshooting

## Quick Start

### 1. Configure Credentials

Run the interactive configuration:
```bash
cos configure
```

You'll be prompted for:
- **Secret ID**: Your Tencent Cloud secret ID
- **Secret Key**: Your Tencent Cloud secret key
- **Assume Role ARN**: (Optional) Role to assume
- **Default Region**: Default region (e.g., ap-shanghai)
- **Default Bucket**: (Optional) Default bucket name
- **Default Prefix**: (Optional) Default prefix
- **Output Format**: json, table, or text

#### Generate Temporary Credentials

For testing or temporary access:
```bash
# Generate 2-hour temporary token
cos token

# Use environment variables
cos token --output env > temp_creds.sh
source temp_creds.sh
```

**📖 More details**: [docs/TOKEN_MANAGEMENT.md](docs/TOKEN_MANAGEMENT.md)

### 2. Basic Commands

#### List Buckets
```bash
cos ls
```

#### List Objects in Bucket
```bash
cos ls cos://my-bucket/
cos ls cos://my-bucket/folder/ --recursive
```

#### Upload Files
```bash
# Upload single file
cos cp local-file.txt cos://my-bucket/remote-file.txt

# Upload directory
cos cp ./local-dir/ cos://my-bucket/remote-dir/ --recursive
```

#### Download Files
```bash
# Download single file
cos cp cos://my-bucket/file.txt ./local-file.txt

# Download directory
cos cp cos://my-bucket/folder/ ./local-folder/ --recursive
```

#### Copy Between Buckets
```bash
cos cp cos://bucket1/file.txt cos://bucket2/file.txt
```

#### Delete Objects
```bash
# Delete single object
cos rm cos://my-bucket/file.txt

# Delete multiple objects
cos rm cos://my-bucket/folder/ --recursive
```

#### Move/Rename Objects
```bash
# Rename object
cos mv cos://bucket/old-name.txt cos://bucket/new-name.txt

# Move directory
cos mv cos://bucket/old-folder/ cos://bucket/new-folder/ --recursive

# Move between buckets
cos mv cos://bucket1/file.txt cos://bucket2/file.txt
```

#### Synchronize Directories
```bash
# Sync local to COS (upload)
cos sync ./local-dir/ cos://bucket/remote-dir/

# Sync COS to local (download)
cos sync cos://bucket/remote-dir/ ./local-dir/

# Sync with delete (exact mirror)
cos sync ./local-dir/ cos://bucket/remote-dir/ --delete

# Preview sync without making changes
cos sync ./local-dir/ cos://bucket/remote-dir/ --dryrun

# Fast sync (compare by size only)
cos sync ./local-dir/ cos://bucket/remote-dir/ --size-only
```

#### Generate Presigned URLs
```bash
# Generate URL for download (default 1 hour)
cos presign cos://bucket/file.txt

# Custom expiration (2 hours)
cos presign cos://bucket/file.txt --expires-in 7200

# Generate upload URL
cos presign cos://bucket/file.txt --method PUT

# Generate short-lived URL (5 minutes)
cos presign cos://bucket/file.txt -e 300
```

#### Create/Delete Buckets
```bash
# Create bucket
cos mb cos://my-new-bucket

# Delete bucket
cos rb cos://my-bucket

# Delete bucket with all contents
cos rb cos://my-bucket --force
```

## Advanced Usage

### Multiple Profiles

Configure multiple profiles for different accounts or environments:

```bash
# Configure production profile
cos configure --profile production

# Use production profile
cos ls --profile production

# Set profile in environment
export COS_PROFILE=production
cos ls
```

### Output Formats

Choose from three output formats:

```bash
# Table format (default)
cos ls cos://bucket/ --output table

# JSON format
cos ls cos://bucket/ --output json

# Text format (for scripting)
cos ls cos://bucket/ --output text
```

### Region Override

```bash
# Override default region
cos ls cos://bucket/ --region ap-beijing

# Set region in environment
export COS_REGION=ap-beijing
```

### Filtering

```bash
# Include specific patterns
cos cp ./dir/ cos://bucket/ --recursive --include "*.txt"

# Exclude specific patterns
cos cp ./dir/ cos://bucket/ --recursive --exclude "*.log"
```

### Progress Control

```bash
# Disable progress bars
cos cp large-file.iso cos://bucket/ --no-progress

# Quiet mode
cos cp file.txt cos://bucket/ --quiet
```

## Configuration

### Configuration Files

Configuration is stored in `~/.cos/`:

```
~/.cos/
├── config          # Configuration settings
└── credentials     # Credentials (secret keys)
```

### Configuration File Format

`~/.cos/config`:
```ini
[default]
region = ap-shanghai
output = json

[profile production]
region = ap-beijing
output = table
```

### Credentials File Format

`~/.cos/credentials`:
```ini
[default]
secret_id = AKIDxxxxx
secret_key = xxxxxxxxx
assume_role = qcs::cam::uin/xxx:roleName/xxx

[profile production]
secret_id = AKIDxxxxx
secret_key = xxxxxxxxx
```

### Environment Variables

Override configuration with environment variables:

```bash
export COS_SECRET_ID=AKIDxxxxx
export COS_SECRET_KEY=xxxxxxxxx
export COS_REGION=ap-shanghai
export COS_ASSUME_ROLE=qcs::cam::uin/xxx:roleName/xxx
export COS_OUTPUT=json
export COS_PROFILE=production
```

## Command Reference

### Global Options

```bash
--profile TEXT              Use specific profile
--region TEXT               Override default region
--output [json|table|text]  Output format
--endpoint-url TEXT         Custom endpoint URL
--no-verify-ssl            Skip SSL verification
--debug                    Enable debug mode
--quiet                    Suppress output
```

### Commands

| Command | Description |
|---------|-------------|
| `configure` | Configure COS CLI settings |
| `ls` | List buckets or objects |
| `cp` | Copy files to/from/within COS |
| `mv` | Move or rename objects |
| `sync` | Synchronize directories between local and COS |
| `rm` | Remove objects |
| `mb` | Make (create) bucket |
| `rb` | Remove bucket |
| `presign` | Generate presigned URLs for temporary access |
| `token` | Generate temporary STS credentials |
| `lifecycle` | Manage bucket lifecycle policies |
| `policy` | Manage bucket access policies |
| `cors` | Configure CORS settings |
| `versioning` | Manage bucket versioning |

## Advanced Commands

### Bucket Lifecycle Management

Control automatic transitions and expiration of objects:

```bash
# View lifecycle rules
cos lifecycle get cos://my-bucket

# Set lifecycle rules from JSON file
cos lifecycle put cos://my-bucket --config lifecycle.json

# Delete lifecycle configuration
cos lifecycle delete cos://my-bucket
```

**Example lifecycle.json**:
```json
{
  "Rule": [
    {
      "ID": "Delete old logs",
      "Status": "Enabled",
      "Filter": {"Prefix": "logs/"},
      "Expiration": {"Days": 30}
    },
    {
      "ID": "Archive to ARCHIVE",
      "Status": "Enabled",
      "Filter": {"Prefix": "archive/"},
      "Transition": {
        "Days": 90,
        "StorageClass": "ARCHIVE"
      }
    }
  ]
}
```

### Bucket Policy Management

Control access permissions at bucket level:

```bash
# View current policy
cos policy get cos://my-bucket

# Set policy from JSON file
cos policy put cos://my-bucket --policy policy.json

# Delete policy
cos policy delete cos://my-bucket
```

**Example policy.json**:
```json
{
  "version": "2.0",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"qcs": ["qcs::cam::uin/100000000001:uin/100000000001"]},
      "Action": ["name/cos:GetObject"],
      "Resource": ["qcs::cos:ap-shanghai:uid/1250000000:my-bucket/*"]
    }
  ]
}
```

### CORS Configuration

Configure Cross-Origin Resource Sharing:

```bash
# View CORS rules
cos cors get cos://my-bucket

# Set CORS rules from JSON file
cos cors put cos://my-bucket --config cors.json

# Delete CORS configuration
cos cors delete cos://my-bucket
```

**Example cors.json**:
```json
{
  "CORSRule": [
    {
      "ID": "Allow all origins",
      "AllowedOrigin": ["*"],
      "AllowedMethod": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedHeader": ["*"],
      "ExposeHeader": ["ETag", "Content-Length"],
      "MaxAgeSeconds": 3600
    }
  ]
}
```

### Bucket Versioning

Enable object versioning for protection:

```bash
# Check versioning status
cos versioning get cos://my-bucket

# Enable versioning
cos versioning enable cos://my-bucket

# Suspend versioning
cos versioning suspend cos://my-bucket
```

### Pattern Matching

Filter files during transfer operations:

```bash
# Upload only Python files
cos cp ./project/ cos://bucket/code/ -r --include "*.py"

# Upload all except tests
cos cp ./project/ cos://bucket/code/ -r --exclude "test_*"

# Complex patterns: include source files, exclude tests and cache
cos cp ./project/ cos://bucket/backup/ -r \
  --include "*.py" --include "*.js" \
  --exclude "test_*" --exclude "__pycache__"

# Download only log files
cos cp cos://bucket/logs/ ./local-logs/ -r --include "*.log"
```

### Checksum Verification

Ensure data integrity with MD5 checksums:

```bash
# Sync with checksum verification
cos sync ./local/ cos://bucket/remote/ --checksum

# Even if timestamps differ, skip files with matching checksums
cos sync ./local/ cos://bucket/remote/ --checksum --size-only
```

## Examples

### Backup Local Directory to COS
```bash
cos cp ./my-data/ cos://my-backup-bucket/$(date +%Y%m%d)/ --recursive
```

### Download Latest Files
```bash
cos ls cos://bucket/logs/ --output text | tail -5 | while read file; do
  cos cp cos://bucket/$file ./
done
```

### Sync Directory
```bash
# Upload only changed files
cos sync ./local-dir/ cos://bucket/backup/ --size-only

# Exact mirror (delete files not in source)
cos sync ./local-dir/ cos://bucket/backup/ --delete
```

### Share Files with Presigned URLs
```bash
# Generate a download link valid for 24 hours
cos presign cos://bucket/document.pdf --expires-in 86400

# Share via curl
URL=$(cos presign cos://bucket/file.txt)
echo "Download: $URL"
```

### Bulk Delete Old Files
```bash
cos ls cos://bucket/archive/ --output text | while read file; do
  cos rm cos://bucket/$file
done
```

## Troubleshooting

### Authentication Errors

If you get authentication errors:
1. Verify credentials: `cos configure list`
2. Check credential file permissions: `ls -la ~/.cos/`
3. Try with debug mode: `cos ls --debug`

### SSL Verification Errors

If you encounter SSL errors:
```bash
cos ls --no-verify-ssl
```

### Large File Uploads

For files larger than 5MB, multipart upload is automatic. For very large files:
- Ensure stable network connection
- Use `--no-progress` for background operations
- Check available disk space

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
black cos/
flake8 cos/
mypy cos/
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Documentation

- **Quick Reference**: [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)
- **Development Plan**: [docs/COS_CLI_DEVELOPMENT_PLAN.md](docs/COS_CLI_DEVELOPMENT_PLAN.md)
- **Implementation Summary (v1.1.0)**: [docs/IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md)
- **Implementation Complete (v2.0.0)**: [docs/IMPLEMENTATION_COMPLETE_V2.md](docs/IMPLEMENTATION_COMPLETE_V2.md)
- **Final Verification Report**: [docs/VERIFICATION_COMPLETE.md](docs/VERIFICATION_COMPLETE.md)
- **Release Notes (v2.0.0)**: [docs/RELEASE_NOTES_2.0.0.md](docs/RELEASE_NOTES_2.0.0.md)
- **Full Index**: [docs/INDEX.md](docs/INDEX.md)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Credits

Built with:
- [uv](https://github.com/astral-sh/uv) - Ultra-fast package installer
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output
- [Tencent Cloud SDK](https://cloud.tencent.com/document/sdk/Python) - Official SDK

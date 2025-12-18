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
- **Output Format**: json, table, or text

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
| `rm` | Remove objects |
| `mb` | Make (create) bucket |
| `rb` | Remove bucket |

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

### Sync Directory (one-way)
```bash
# Upload only changed files
for file in $(find ./local-dir -type f); do
  cos cp $file cos://bucket/${file#./local-dir/}
done
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
- **Full Index**: [docs/INDEX.md](docs/INDEX.md)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Credits

Built with:
- [uv](https://github.com/astral-sh/uv) - Ultra-fast package installer
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output
- [Tencent Cloud SDK](https://cloud.tencent.com/document/sdk/Python) - Official SDK

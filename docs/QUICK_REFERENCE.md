# COS CLI - Quick Reference Guide

## Installation

```bash
# Quick install (uses uv - 10-100x faster!)
./install.sh

# Or with virtual environment
./install-uv.sh
source .venv/bin/activate

# Or manually with uv
uv pip install -e .

# Or traditional pip
pip install -e .

# Verify installation
cos --version
cos --help
```

**Note**: We now use `uv` for faster package management. See [UV_GUIDE.md](UV_GUIDE.md).

## Initial Setup

```bash
# Configure credentials (interactive)
cos configure

# Or configure for specific profile
cos configure --profile production
```

## Common Commands

### List Operations
```bash
# List all buckets
cos ls

# List objects in bucket
cos ls cos://my-bucket/

# List with prefix
cos ls cos://my-bucket/folder/

# Recursive listing
cos ls cos://my-bucket/ --recursive

# Human-readable sizes
cos ls cos://my-bucket/ --human-readable
```

### Upload Files
```bash
# Upload single file
cos cp file.txt cos://bucket/file.txt

# Upload directory
cos cp ./local-dir/ cos://bucket/remote-dir/ --recursive

# Upload with progress disabled
cos cp large-file.iso cos://bucket/ --no-progress
```

### Download Files
```bash
# Download single file
cos cp cos://bucket/file.txt ./local.txt

# Download directory
cos cp cos://bucket/folder/ ./local-folder/ --recursive
```

### Copy Between Buckets
```bash
# Copy single object
cos cp cos://bucket1/file.txt cos://bucket2/file.txt

# Copy directory
cos cp cos://bucket1/folder/ cos://bucket2/folder/ --recursive
```

### Delete Operations
```bash
# Delete single object
cos rm cos://bucket/file.txt

# Delete multiple objects (with prefix)
cos rm cos://bucket/folder/ --recursive

# Dry run (preview deletion)
cos rm cos://bucket/folder/ --recursive --dryrun
```

### Move/Rename Objects
```bash
# Rename single object
cos mv cos://bucket/old-name.txt cos://bucket/new-name.txt

# Move directory
cos mv cos://bucket/old-folder/ cos://bucket/new-folder/ --recursive

# Move between buckets
cos mv cos://bucket1/file.txt cos://bucket2/file.txt

# Move with confirmation
cos mv cos://bucket/source/ cos://bucket/dest/ --recursive
```

### Synchronize Directories
```bash
# Sync local to COS (upload changed files)
cos sync ./local-dir/ cos://bucket/remote-dir/

# Sync COS to local (download)
cos sync cos://bucket/remote-dir/ ./local-dir/

# Sync with delete (exact mirror)
cos sync ./local-dir/ cos://bucket/remote-dir/ --delete

# Preview changes without execution
cos sync ./local-dir/ cos://bucket/remote-dir/ --dryrun

# Fast sync (compare by size only, skip time check)
cos sync ./local-dir/ cos://bucket/remote-dir/ --size-only

# Combine options
cos sync ./local-dir/ cos://bucket/backup/ --delete --size-only
```

### Generate Presigned URLs
```bash
# Generate download URL (default 1 hour)
cos presign cos://bucket/file.txt

# Custom expiration (2 hours = 7200 seconds)
cos presign cos://bucket/file.txt --expires-in 7200

# Short-lived URL (5 minutes)
cos presign cos://bucket/file.txt -e 300

# Long-lived URL (7 days, maximum)
cos presign cos://bucket/file.txt -e 604800

# Generate upload URL
cos presign cos://bucket/file.txt --method PUT

# Generate delete URL
cos presign cos://bucket/file.txt --method DELETE
```

### Token Management
```bash
# Generate temporary credentials (default 2 hours)
cos token

# Custom duration (8 hours)
cos token --duration 28800

# Output as environment variables
cos token --output env > temp_creds.sh
source temp_creds.sh

# JSON format
cos token --output json

# Import token directly into config
cos configure import-token
```

### Bucket Management
```bash
# Create bucket
cos mb cos://new-bucket

# Create bucket in specific region
cos mb cos://new-bucket --region ap-beijing

# Delete empty bucket
cos rb cos://old-bucket

# Delete bucket with all contents
cos rb cos://old-bucket --force
```

## Configuration

### View Configuration
```bash
# List all settings
cos configure list

# Get specific value
cos configure get region
```

### Set Configuration
```bash
# Set region
cos configure set region ap-shanghai

# Set output format
cos configure set output json
```

### Multiple Profiles
```bash
# Configure production profile
cos configure --profile production

# Use profile in commands
cos ls --profile production

# Set default profile via environment
export COS_PROFILE=production
cos ls
```

## Output Formats

```bash
# Table format (default)
cos ls cos://bucket/ --output table

# JSON format (machine-readable)
cos ls cos://bucket/ --output json

# Text format (for scripting)
cos ls cos://bucket/ --output text
```

## Global Options

```bash
--profile TEXT              # Use specific profile
--region TEXT               # Override region
--output [json|table|text]  # Output format
--endpoint-url TEXT         # Custom endpoint
--no-verify-ssl            # Skip SSL verification
--debug                    # Debug mode
--quiet                    # Quiet mode
--no-progress             # Disable progress bars
```

## Transfer Tuning (Cheat Sheet)

| Flag | Default | Applies To | Notes |
|------|---------|------------|-------|
| `--concurrency` | `4` | `cp -r` | Parallel workers for recursive transfers |
| `--part-size` | `8MB` | `cp`, `mv` (local→COS), `sync` | Per-part size for multipart and ranged |
| `--max-retries` | `3` | `cp`, `mv`, `sync` | Retries per part/range |
| `--retry-backoff` | `0.5s` | `cp`, `mv`, `sync` | Initial backoff (exponential) |
| `--retry-backoff-max` | `5.0s` | `cp`, `mv`, `sync` | Maximum backoff cap |
| `--resume/--no-resume` | `--resume` | `cp`/`sync` downloads | Resume ranged downloads |

Examples:

```bash
# Tune part size and retries for a large download
cos cp cos://bucket/large.tar.gz ./ --part-size 64MB --max-retries 5 --retry-backoff 1.0 --retry-backoff-max 10.0

# Local to COS move with larger parts
cos mv ./big.bin cos://bucket/big.bin --part-size 64MB --max-retries 5

# Sync with resumable ranged downloads
cos sync cos://bucket/remote/ ./local/ --part-size 64MB --resume
```

## Environment Variables

```bash
export COS_SECRET_ID=AKID...
export COS_SECRET_KEY=...
export COS_REGION=ap-shanghai
export COS_ASSUME_ROLE=qcs::cam::uin/xxx:roleName/xxx
export COS_OUTPUT=json
export COS_PROFILE=production
export COS_ENDPOINT_URL=https://...
```

## Practical Examples

### Backup Directory
```bash
# Backup with timestamp
cos cp ./important-data/ \
  cos://backup-bucket/backup-$(date +%Y%m%d)/ \
  --recursive
```

### Download Latest Files
```bash
# Get last 5 files
cos ls cos://bucket/logs/ --output text | tail -5 | \
  while read file; do
    cos cp cos://bucket/$file ./
  done
```

### Bulk Delete
```bash
# Preview what will be deleted
cos rm cos://bucket/temp/ --recursive --dryrun

# Actually delete
cos rm cos://bucket/temp/ --recursive
```

### Sync Operation
```bash
# Sync directory (proper bidirectional sync)
cos sync ./local/ cos://bucket/backup/

# Preview sync changes
cos sync ./local/ cos://bucket/backup/ --dryrun

# Exact mirror (delete extra files)
cos sync ./local/ cos://bucket/backup/ --delete
```

### Share Files with Presigned URLs
```bash
# Generate shareable link
URL=$(cos presign cos://bucket/document.pdf --expires-in 86400)
echo "Share this link: $URL"

# Download with curl
cos presign cos://bucket/file.txt | xargs curl -O

# Upload with presigned URL
UPLOAD_URL=$(cos presign cos://bucket/new-file.txt --method PUT)
curl -X PUT -T local-file.txt "$UPLOAD_URL"
```

### List with Filtering
```bash
# List only text files (requires jq)
cos ls cos://bucket/ --output json | \
  jq -r '.[] | select(.Key | endswith(".txt")) | .Key'
```

## Troubleshooting

### Debug Mode
```bash
# Enable debug output
cos ls --debug
```

### Check Configuration
```bash
# View all settings
cos configure list

# Check specific setting
cos configure get region
```

### SSL Issues
```bash
# Disable SSL verification
cos ls --no-verify-ssl
```

### Authentication Issues
```bash
# Reconfigure credentials
cos configure

# Check credentials file permissions
ls -la ~/.cos/
```

## File Locations

- **Config Directory**: `~/.cos/`
- **Config File**: `~/.cos/config`
- **Credentials File**: `~/.cos/credentials`

## Tips & Tricks

### 1. Use Profiles for Different Accounts
```bash
cos configure --profile personal
cos configure --profile work
cos ls --profile work
```

### 2. JSON Output for Processing
```bash
# Count objects
cos ls cos://bucket/ --output json | jq '. | length'

# Get total size
cos ls cos://bucket/ --output json | \
  jq '[.[].Size] | add'
```

### 3. Quiet Mode for Scripts
```bash
if cos cp file.txt cos://bucket/ --quiet; then
  echo "Upload successful"
fi
```

### 4. Batch Upload
```bash
find ./photos -name "*.jpg" | while read photo; do
  cos cp "$photo" cos://photos-bucket/
done
```

### 5. Download to Stdout (future feature)
```bash
# When implemented:
cos cp cos://bucket/file.txt - | grep "pattern"
```

## Command Aliases (Add to ~/.bashrc)

```bash
# Short aliases
alias cl='cos ls'
alias ccp='cos cp'
alias crm='cos rm'

# Useful combinations
alias cls='cos ls --human-readable'
alias cjson='cos ls --output json'
```

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Configuration error
- `3` - Authentication error

## Getting Help

```bash
# General help
cos --help

# Command-specific help
cos ls --help
cos cp --help
cos configure --help
```

## Version Information

```bash
# Check version
cos --version
```

## Advanced Use Cases

### Mirror Bucket (Manual Sync)
```bash
# Create local mirror
cos cp cos://source-bucket/ ./mirror/ --recursive

# Upload changes back
cos cp ./mirror/ cos://dest-bucket/ --recursive
```

### Generate File List
```bash
# Export object list to file
cos ls cos://bucket/ --output text > objects.txt

# Process list
cat objects.txt | xargs -I {} cos cp cos://bucket/{} ./backup/
```

### Conditional Operations
```bash
# Upload only if doesn't exist (requires checking)
if ! cos ls cos://bucket/file.txt --output text | grep -q "file.txt"; then
  cos cp local-file.txt cos://bucket/file.txt
fi
```

---

**For more information:**
- Full documentation: `README.md`
- Development plan: `COS_CLI_DEVELOPMENT_PLAN.md`
- Project summary: `PROJECT_SUMMARY.md`

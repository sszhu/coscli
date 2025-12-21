# Token Usage Guide

## Generating Clean Environment Variable Files

The `cos token --output env` command now properly separates informational messages from the actual export statements.

### Correct Usage

```bash
# Generate credentials file (info goes to stderr, exports to stdout)
cos token --output env > temp_creds.sh

# The file will now be clean and sourceable
cat temp_creds.sh
# Output:
# # Export these environment variables to use temporary credentials
# export COS_SECRET_ID='AKID...'
# export COS_SECRET_KEY='...'
# export COS_TOKEN='...'
# # Valid until: 2025-12-21 14:01:15

# Source the file
source temp_creds.sh

# Verify credentials are set
echo $COS_SECRET_ID
```

### What Changed (v1.1.0+)

**Before:** Info messages were mixed with export statements
```bash
$ cos token --output env > temp_creds.sh
$ cat temp_creds.sh
ℹ Generating temporary credentials (duration: 7200s)...
# Export these environment variables...
export COS_SECRET_ID='...'
✓ Temporary credentials generated successfully
```
❌ Cannot source - contains non-shell syntax

**After:** Info messages go to stderr
```bash
$ cos token --output env > temp_creds.sh
ℹ Generating temporary credentials (duration: 7200s)...  # <- stderr
✓ Temporary credentials generated successfully            # <- stderr

$ cat temp_creds.sh
# Export these environment variables...
export COS_SECRET_ID='...'
export COS_SECRET_KEY='...'
export COS_TOKEN='...'
# Valid until: 2025-12-21 14:01:15
```
✅ Clean shell script - can be sourced

### Capture Both Stdout and Stderr

```bash
# Save exports to file, but see progress on screen
cos token --output env > temp_creds.sh

# Or capture both
cos token --output env > temp_creds.sh 2>&1
# Note: This will include info messages in the file (not sourceable)

# Better: Redirect stderr to terminal, stdout to file
cos token --output env 2>/dev/tty > temp_creds.sh
```

### Using in Web UI

The Web UI can use temporary tokens from environment variables:

**Option 1: Set environment variables before starting UI**
```bash
# Generate and source credentials
cos token --output env > temp_creds.sh
source temp_creds.sh

# Start UI (will use env vars)
python ui/app.py
```

**Option 2: Use process substitution**
```bash
# Source credentials in the same command
source <(cos token --output env) && python ui/app.py
```

**Option 3: Docker/Container usage**
```bash
# Generate credentials
cos token --output env > temp_creds.sh

# Run container with environment variables
docker run --env-file temp_creds.sh my-ui-image
```

### Troubleshooting

**Error: "assume_role ARN is required"**
```bash
# Configure assume role first
cos configure
# Enter your assume_role ARN when prompted

# Or set it directly
cos configure set assume_role qcs::cam::uin/123456:roleName/MyRole
```

**Expired credentials**
```bash
# Check expiration (stored in file comments)
grep "Valid until" temp_creds.sh

# Regenerate if expired
cos token --output env > temp_creds.sh
source temp_creds.sh
```

**Credentials not being used**
```bash
# Verify environment variables are set
env | grep COS_

# Expected output:
# COS_SECRET_ID=AKID...
# COS_SECRET_KEY=...
# COS_TOKEN=...

# Test with a simple command
cos ls
```

### Security Best Practices

1. **Don't commit credential files**
   ```bash
   # Add to .gitignore
   echo "temp_creds.sh" >> .gitignore
   echo "*_creds.sh" >> .gitignore
   ```

2. **Use short durations for sensitive operations**
   ```bash
   # 1 hour token
   cos token --duration 3600 --output env > temp_creds.sh
   ```

3. **Clean up after use**
   ```bash
   # Unset variables
   unset COS_SECRET_ID COS_SECRET_KEY COS_TOKEN
   
   # Remove file
   rm temp_creds.sh
   ```

4. **Use separate tokens for different purposes**
   ```bash
   # UI token (longer duration)
   cos token --duration 28800 --output env > ui_creds.sh
   
   # Script token (shorter duration)
   cos token --duration 3600 --output env > script_creds.sh
   ```

### Integration Examples

**CI/CD Pipeline**
```bash
#!/bin/bash
# .github/workflows/deploy.sh

# Generate temporary credentials
cos token --duration 3600 --output env > /tmp/cos_creds.sh
source /tmp/cos_creds.sh

# Run deployment
python deploy.py

# Cleanup
rm /tmp/cos_creds.sh
unset COS_SECRET_ID COS_SECRET_KEY COS_TOKEN
```

**Systemd Service**
```ini
[Unit]
Description=Web UI Service
After=network.target

[Service]
Type=simple
ExecStartPre=/usr/local/bin/cos token --output env > /tmp/ui_creds.sh
ExecStart=/bin/bash -c 'source /tmp/ui_creds.sh && python /app/ui/app.py'
ExecStopPost=/bin/rm /tmp/ui_creds.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

**Automated Token Refresh**
```bash
#!/bin/bash
# refresh_token.sh - Run via cron every 2 hours

CREDS_FILE="/var/run/cos_creds.sh"

# Generate new token (valid for 3 hours)
cos token --duration 10800 --output env > "${CREDS_FILE}.new"

# Atomic replace
mv "${CREDS_FILE}.new" "${CREDS_FILE}"

# Restart services that use it
systemctl reload webapp
```

### Advanced Usage

**Multiple Profiles**
```bash
# Generate tokens for different profiles
cos token --profile prod --output env > prod_creds.sh
cos token --profile dev --output env > dev_creds.sh

# Use specific profile
source prod_creds.sh
cos ls  # Uses prod credentials
```

**Token Chaining**
```bash
# Use one token to generate another (token rotation)
source current_creds.sh
cos token --duration 7200 --output env > new_creds.sh
source new_creds.sh
```

**JSON Output for Programmatic Use**
```bash
# Get JSON output
cos token --output json > token.json

# Parse with jq
TMP_ID=$(jq -r '.Credentials.TmpSecretId' token.json)
TMP_KEY=$(jq -r '.Credentials.TmpSecretKey' token.json)
TOKEN=$(jq -r '.Credentials.Token' token.json)

export COS_SECRET_ID="$TMP_ID"
export COS_SECRET_KEY="$TMP_KEY"
export COS_TOKEN="$TOKEN"
```

## See Also

- [Token Management Guide](TOKEN_MANAGEMENT.md) - Detailed token documentation
- [Quick Reference](QUICK_REFERENCE.md) - Command cheat sheet
- [README](../README.md) - Full documentation

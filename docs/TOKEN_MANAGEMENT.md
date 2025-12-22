# Token Generation and Management

COS CLI supports generating and using temporary STS credentials for testing and temporary access scenarios.

## Overview

Temporary tokens are useful for:
- **Testing access** without permanently storing credentials
- **Sharing access** with team members for limited time
- **CI/CD pipelines** that need short-lived credentials
- **Development environments** with rotating credentials

## Generating Temporary Tokens

### Basic Usage

```bash
# Generate token with default 2-hour duration
cos token

# Generate token with custom duration (1 hour)
cos token --duration 3600

# Generate 30-minute token
cos token --duration 1800
```

### Output Formats

#### Table Format (Default)
```bash
cos token --output table
```
Output:
```
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Key          ┃ Value                           ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ TmpSecretId  │ AKID5oqPTcGsugPfRZaP...         │
│ TmpSecretKey │ ZQpBZSn0eJ8Yy44RzUrR...         │
│ Token        │ sY2bVpEid17JGcKSWg1h1NRwG...    │
│ Duration     │ 3600s (1h 0m)                   │
│ Expires At   │ 2025-12-18 07:35:42             │
└──────────────┴─────────────────────────────────┘
```

#### Environment Variables Format
```bash
cos token --output env
```
Output:
```bash
# Export these environment variables to use temporary credentials
export COS_SECRET_ID='AKIDObfKXzHBRrpwUd3PQKspgP...'
export COS_SECRET_KEY='bU6k72X4irUo1RH5jlxVjzLd/...'
export COS_TOKEN='sY2bVpEid17JGcKSWg1h1NRwGWRM1...'
# Valid until: 2025-12-18 07:36:10
```

#### JSON Format
```bash
cos token --output json
```
Output:
```json
{
  "Credentials": {
    "TmpSecretId": "AKIDE8lZn0sL3m5wqXl70Uzf...",
    "TmpSecretKey": "97iywm0MIT6RjdVQ+mO4f/6RG...",
    "Token": "W9rsDbgWqANRZ1WwDrXHtxkzIb...",
    "Expiration": "2025-12-18T07:06:26.586881"
  },
  "ExpiresIn": 1800,
  "RequestedTime": "2025-12-18T06:36:26.586897"
}
```

## Using Temporary Tokens

### Method 1: Environment Variables (Recommended)

```bash
# Generate and export credentials
cos token --output env > temp_creds.sh
source temp_creds.sh

# Now use cos commands normally
cos ls cos://bucket/
cos cp file.txt cos://bucket/
```

### Method 2: Import to Profile

```bash
# Generate token
TOKEN_OUTPUT=$(cos token --output json)

# Extract values and import
TMP_ID=$(echo $TOKEN_OUTPUT | jq -r '.Credentials.TmpSecretId')
TMP_KEY=$(echo $TOKEN_OUTPUT | jq -r '.Credentials.TmpSecretKey')
TOKEN=$(echo $TOKEN_OUTPUT | jq -r '.Credentials.Token')

# Import to temp profile
cos configure import-token \
  --tmp-secret-id "$TMP_ID" \
  --tmp-secret-key "$TMP_KEY" \
  --token "$TOKEN" \
  --profile temp

# Use with the temp profile
cos ls --profile temp
```

### Method 3: Quick Import (Simplified)

```bash
# Generate and save to file
cos token --output env > temp_creds.sh

# Source it
source temp_creds.sh

# Import using environment variables
cos configure import-token \
  --tmp-secret-id "$COS_SECRET_ID" \
  --tmp-secret-key "$COS_SECRET_KEY" \
  --token "$COS_TOKEN"
```

## Token Duration

- **Minimum**: 1800 seconds (30 minutes)
- **Default**: 7200 seconds (2 hours)
- **Maximum**: 43200 seconds (12 hours)

```bash
# 30-minute token (minimum)
cos token --duration 1800

# 2-hour token (default)
cos token --duration 7200

# 12-hour token (maximum)
cos token --duration 43200
```

## Use Cases

### 1. Testing Access Without Permanent Credentials

```bash
# Generate short-lived token for testing
cos token --duration 1800 --output env > test_creds.sh
source test_creds.sh

# Test operations
cos ls cos://bucket/
cos cp test.txt cos://bucket/test.txt

# Clean up (credentials expire automatically)
unset COS_SECRET_ID COS_SECRET_KEY COS_TOKEN
```

### 2. Sharing Access with Team Members

```bash
# Generate token and share the output
cos token --duration 7200 --output env

# Team member sources the credentials
source shared_creds.sh

# They can now access COS for 2 hours
cos ls cos://shared-bucket/
```

### 3. CI/CD Pipeline

```yaml
# Example GitHub Actions workflow
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Generate COS Token
        run: |
          cos token --duration 3600 --output env >> $GITHUB_ENV
      
      - name: Upload to COS
        run: |
          cos cp dist/* cos://bucket/release/
```

### 4. Development Environment

```bash
# Add to your project's setup script
#!/bin/bash

# Generate daily token
if [ ! -f .cos_token ] || [ $(find .cos_token -mmin +60) ]; then
    echo "Generating new COS token..."
    cos token --duration 7200 --output env > .cos_token
fi

# Source it
source .cos_token

echo "COS credentials loaded (valid for 2 hours)"
```

## Requirements

To use token generation:
1. Must have permanent credentials configured
2. Must have an `assume_role` ARN set
3. The role must have appropriate permissions

Check your configuration:
```bash
cos configure list
```

Ensure these are set:
- `secret_id`: Your permanent secret ID
- `secret_key`: Your permanent secret key
- `assume_role`: Role ARN (e.g., `qcs::cam::uin/xxx:roleName/YourRole`)

## Troubleshooting

### Error: "Assume role ARN is required"

You need to set the assume role in your configuration:
```bash
cos configure set assume_role "qcs::cam::uin/1234567890:roleName/YourRole"
```

### Error: "Duration must be at least 1800 seconds"

Use a duration of at least 30 minutes:
```bash
cos token --duration 1800
```

### Error: "Duration cannot exceed 43200 seconds"

Maximum duration is 12 hours:
```bash
cos token --duration 43200
```

### Token Expired

Tokens are time-limited. Generate a new one:
```bash
# Check when token expires
cos token  # Shows expiration time

# Generate new token
cos token --output env > temp_creds.sh
source temp_creds.sh
```

## Security Best Practices

1. **Never commit tokens** to version control
   ```bash
   # Add to .gitignore
   echo "temp_creds.sh" >> .gitignore
   echo ".cos_token" >> .gitignore
   ```

2. **Use minimum necessary duration**
   ```bash
   # For quick tests, use 30 minutes
   cos token --duration 1800
   ```

3. **Rotate tokens regularly**
   ```bash
   # Automated rotation script
   */30 * * * * /path/to/rotate_token.sh
   ```

4. **Clean up after use**
   ```bash
   # Unset environment variables
   unset COS_SECRET_ID COS_SECRET_KEY COS_TOKEN
   
   # Remove credential files
   rm -f temp_creds.sh .cos_token
   ```

5. **Use profiles for isolation**
   ```bash
   # Import to separate profile
   cos configure import-token --profile temp ...
   
   # Use explicitly
   cos ls --profile temp
   ```

## Command Reference

```bash
# Generate token
cos token [OPTIONS]

Options:
  -d, --duration INTEGER         Token duration in seconds (default: 7200, max: 43200)
  --profile TEXT                 Profile name
  -o, --output [json|table|env]  Output format

# Import token
cos configure import-token [OPTIONS]

Options:
  --tmp-secret-id TEXT   Temporary Secret ID (required)
  --tmp-secret-key TEXT  Temporary Secret Key (required)
  --token TEXT          Security Token (required)
  --profile TEXT        Profile name (default: temp)
```

## Related Documentation

- [Configuration Guide](../README.md#configuration)
- [Authentication](../README.md#authentication)
- [Quick Reference](QUICK_REFERENCE.md)

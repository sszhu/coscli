# COS CLI Credential Precedence Rules

**Version:** 2.2.0  
**Date:** December 22, 2025

---

## Overview

The COS CLI supports multiple ways to provide credentials. When multiple credential sources are configured, a clear precedence order determines which credentials are used.

## Credential Precedence Order

The credential resolution follows this strict priority (highest to lowest):

### 1. **Environment Variables with Temporary Token** (Highest Priority)

When `COS_TOKEN` is set, the CLI uses **ONLY** environment variables and **ignores** all config file settings.

**Required Environment Variables:**
```bash
export COS_SECRET_ID='AKID...'
export COS_SECRET_KEY='...'
export COS_TOKEN='...'
```

**Behavior:**
- ✅ Uses these temporary credentials directly
- ⚠️ Ignores config file `assume_role` setting (prevents conflicts)
- ⚠️ Ignores config file `secret_id` and `secret_key`
- ⏱️ Token has expiration time (typically 30 minutes - 2 hours)

**Use Case:** Quick temporary access from `cos token --output env`

**Example:**
```bash
# Generate and use temporary credentials
cos token --bucket mybucket --prefix "data/" --output env > temp_creds.sh
source temp_creds.sh

# Now all cos commands use these temporary credentials
cos ls cos://mybucket/data/
```

---

### 2. **Config File Temporary Token**

When a temporary token is stored in the config file via `cos configure import-token`.

**Config File Location:** `~/.cos/credentials`
```ini
[profile_name]
secret_id = AKID...
secret_key = ...
token = ...
```

**Behavior:**
- ✅ Uses token from config file
- ⚠️ Ignores `assume_role` in config (token takes precedence)
- ⏱️ Token has expiration time

**Use Case:** Store temporary credentials for repeated use

**Example:**
```bash
# Import temporary credentials to profile
cos configure import-token \
  --tmp-secret-id $TEMP_ID \
  --tmp-secret-key $TEMP_KEY \
  --token $TOKEN \
  --profile temp

# Use with profile
cos ls --profile temp
```

---

### 3. **STS via Assume Role**

When `assume_role` is configured but no temporary token is present.

**Config File:** `~/.cos/credentials`
```ini
[default]
secret_id = AKID...      # Your permanent credentials
secret_key = ...
assume_role = qcs::cam::uin/123456:roleName/MyRole
```

**Behavior:**
- ✅ Uses permanent credentials to call STS AssumeRole
- ✅ Automatically generates temporary credentials
- ✅ Caches temporary credentials (auto-refresh on expiry)
- 🔒 Requires CAM role trust policy to allow assumption

**Use Case:** Assume a role with limited permissions

**Example:**
```bash
cos configure set assume_role "qcs::cam::uin/123456:roleName/ReadOnlyRole"
cos ls  # Automatically assumes role and lists
```

---

### 4. **Permanent Credentials** (Lowest Priority)

When no token or assume_role is configured.

**Config File:** `~/.cos/credentials`
```ini
[default]
secret_id = AKID...
secret_key = ...
```

**Or Environment Variables:**
```bash
export COS_SECRET_ID='AKID...'
export COS_SECRET_KEY='...'
```

**Behavior:**
- ✅ Uses these credentials directly
- ⚠️ No expiration (permanent access)
- 🔒 Full account permissions (unless restricted by CAM policies)

**Use Case:** Long-term automation, personal workstation

**Example:**
```bash
cos configure
# Enter secret_id and secret_key
cos ls  # Uses permanent credentials
```

---

## Conflict Resolution

### Scenario 1: Environment Token + Config Assume Role

**Configuration:**
```bash
# Config file
[default]
assume_role = qcs::cam::uin/123:roleName/MyRole  # ← This will be IGNORED

# Environment
export COS_TOKEN='...'  # ← This takes precedence
export COS_SECRET_ID='AKID_temp...'
export COS_SECRET_KEY='...'
```

**Result:** Uses environment token, **ignores** config `assume_role`

**Why:** Temporary tokens from environment are considered explicit user intent and override all config file settings.

---

### Scenario 2: Config Token + Config Assume Role

**Configuration:**
```ini
[default]
secret_id = AKID...
secret_key = ...
token = TOKEN...          # ← This takes precedence
assume_role = qcs::...   # ← This will be IGNORED
```

**Result:** Uses config token, **ignores** assume_role

**Why:** Existing temporary token takes precedence over generating new one via assume_role.

---

### Scenario 3: Environment Secret + Config Assume Role

**Configuration:**
```bash
# Environment (no COS_TOKEN)
export COS_SECRET_ID='AKID...'
export COS_SECRET_KEY='...'

# Config file
[default]
assume_role = qcs::cam::uin/123:roleName/MyRole
```

**Result:** Uses environment credentials to **assume the role** from config

**Why:** Environment credentials override config credentials, but assume_role logic still applies.

---

## Best Practices

### ✅ DO

1. **Use environment variables for temporary access:**
   ```bash
   cos token --bucket mybucket --prefix "temp/" --output env > /tmp/creds.sh
   source /tmp/creds.sh
   cos cp file.txt cos://mybucket/temp/
   unset COS_TOKEN COS_SECRET_ID COS_SECRET_KEY  # Clean up
   ```

2. **Use config file for permanent/repeated access:**
   ```bash
   cos configure  # Set permanent credentials
   cos ls
   ```

3. **Use profiles for multiple accounts:**
   ```bash
   cos configure --profile production
   cos configure --profile development
   cos ls --profile production
   ```

4. **Use assume_role for restricted access:**
   ```bash
   cos configure set assume_role "qcs::cam::uin/123:roleName/ReadOnly"
   ```

### ❌ DON'T

1. **Mix environment tokens with config assume_role:**
   ```bash
   # BAD: Confusing and may not work as expected
   export COS_TOKEN='...'  # From old session
   # Config has assume_role set
   cos ls  # Which one is used? ← Environment token wins, but confusing!
   ```

   **Fix:** Clear environment variables if using config:
   ```bash
   unset COS_TOKEN COS_SECRET_ID COS_SECRET_KEY
   cos ls  # Now clearly uses config assume_role
   ```

2. **Leave expired tokens in environment:**
   ```bash
   # BAD: Token expires after 30 minutes
   source temp_creds.sh
   # ... 40 minutes later ...
   cos ls  # ← Fails with expired token error
   ```

   **Fix:** Always check token expiration or regenerate:
   ```bash
   cos token --bucket mybucket --output env | grep "Valid until"
   ```

3. **Store temporary tokens in config file for long-term use:**
   ```bash
   # BAD: Tokens expire
   cos configure import-token ...  # Token valid for 30 min
   # ... next day ...
   cos ls  # ← Fails
   ```

   **Fix:** Use `assume_role` for automated/long-term use:
   ```bash
   cos configure set assume_role "qcs::cam::uin/123:roleName/MyRole"
   cos ls  # Auto-generates fresh tokens as needed
   ```

---

## Checking Active Credentials

### View Current Configuration
```bash
# See what's in config file (credentials are masked)
cos configure list

# Check environment variables
env | grep COS_
```

### Understand Which Credentials Will Be Used

```bash
# If COS_TOKEN is set in environment
if [ -n "$COS_TOKEN" ]; then
  echo "Using: Environment temporary token"
  echo "Valid until: Check output from token generation"
  
# If token in config file
elif grep -q "^token" ~/.cos/credentials; then
  echo "Using: Config file temporary token"
  echo "⚠️  Check if expired"
  
# If assume_role in config
elif cos configure get assume_role 2>/dev/null; then
  echo "Using: STS via assume_role"
  echo "✅ Auto-refreshes on expiration"
  
# Otherwise
else
  echo "Using: Permanent credentials"
fi
```

---

## Troubleshooting

### Error: "Access Denied" after sourcing credentials

**Cause:** Token has expired

**Solution:**
```bash
# Check when token expires (from original token output)
# Regenerate token
cos token --bucket mybucket --output env > temp_creds.sh
source temp_creds.sh
```

### Error: "Credentials not found"

**Cause:** No credentials configured

**Solution:**
```bash
cos configure  # Set up credentials
```

### Commands work then suddenly fail

**Cause:** Mixed credential sources with different permissions

**Solution:**
```bash
# Clear environment to use config file
unset COS_TOKEN COS_SECRET_ID COS_SECRET_KEY COS_ASSUME_ROLE

# Check what's in config
cos configure list

# Reconfigure if needed
cos configure
```

### Different behavior with --profile

**Cause:** Profile uses different credential source

**Solution:**
```bash
# Check specific profile
cos configure list --profile myprofile

# Environment variables affect ALL profiles
# To use profile credentials, clear environment:
unset COS_TOKEN COS_SECRET_ID COS_SECRET_KEY
cos ls --profile myprofile
```

---

## Summary Table

| Source | Priority | Behavior | Expiration | Use Case |
|--------|----------|----------|------------|----------|
| `COS_TOKEN` + env vars | 1 (Highest) | Direct use | Yes (30m-2h) | Temporary restricted access |
| Config file `token` | 2 | Direct use | Yes (30m-2h) | Repeated temp access |
| Config `assume_role` | 3 | Generates STS | Yes (auto-refresh) | Long-term restricted access |
| Permanent credentials | 4 (Lowest) | Direct use | No | Full account access |

---

## Version History

- **2.2.0** (2025-12-22): Fixed credential conflict resolution, added clear precedence rules
- **2.0.1** (2025-12-21): Initial credential management implementation

---

## Related Documentation

- [Token Management Guide](TOKEN_MANAGEMENT.md)
- [STS Prefix Access Guide](STS_PREFIX_ACCESS_GUIDE.md)
- [Configuration Guide](../README.md#configuration)

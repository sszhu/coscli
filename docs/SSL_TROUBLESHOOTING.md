# SSL Certificate Troubleshooting Guide

This guide helps resolve SSL certificate issues during COS CLI installation and usage, commonly encountered in corporate networks with SSL inspection.

## Problem 1: Installation Error - SSL Certificate During uv Installation

### Error Message
```
curl: (60) SSL certificate problem: self signed certificate in certificate chain
curl failed to verify the legitimacy of the server and therefore could not
establish a secure connection to it.
```

### Solution A: Updated install.sh (Recommended)

The latest `install.sh` automatically handles this. Update your installation script:

```bash
# Pull latest changes
git pull origin main

# Run installation
./install.sh
```

The script now automatically retries with `--insecure` if SSL verification fails.

### Solution B: Manual Installation with SSL Workaround

If the automatic retry doesn't work, install manually:

```bash
# Install uv with insecure flag
curl -LsSfk https://astral.sh/uv/install.sh | sh

# Activate cargo environment
source "$HOME/.cargo/env"

# Verify uv is installed
uv --version

# Create virtual environment
cd /path/to/coscli
uv venv

# Activate environment
source .venv/bin/activate

# Install COS CLI with native TLS
uv pip install -e . --native-tls
```

### Solution C: Use System Python pip (Fallback)

If uv installation continues to fail:

```bash
# Create venv with system Python
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install COS CLI
pip install -e .
```

## Problem 2: SSL Error When Using COS CLI

### Error Message
```
Error: Failed to authenticate: STS authentication failed:
[TencentCloudSDKException] code:ClientNetworkError
message:HTTPSConnectionPool(host='sts.tencentcloudapi.com', port=443):
Max retries exceeded with url: / (Caused by
SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED]
certificate verify failed: self-signed certificate in certificate chain')))
```

### Solution: Already Handled!

COS CLI v1.0.2+ automatically disables SSL verification for Tencent Cloud APIs. This is configured in `cos/auth.py` and should work out of the box.

**If you still see this error:**

1. **Ensure you have the latest version:**
   ```bash
   cd /path/to/coscli
   git pull origin main
   
   # Reinstall
   source .venv/bin/activate
   pip install -e . --force-reinstall
   ```

2. **Verify the auth.py patch is present:**
   ```bash
   grep -A 5 "patched_request" cos/auth.py
   ```
   
   You should see the SSL verification bypass code.

## Environment-Specific Solutions

### Corporate Network with Proxy

If your organization uses a proxy:

```bash
# Set proxy environment variables
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"
export NO_PROXY="localhost,127.0.0.1"

# Then run installation
./install.sh
```

### Custom CA Certificates

If your organization has custom CA certificates:

```bash
# Option 1: Set CA bundle path
export REQUESTS_CA_BUNDLE=/path/to/company-ca-bundle.crt
export CURL_CA_BUNDLE=/path/to/company-ca-bundle.crt

# Option 2: Use system certificates
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
```

### macOS Specific

On macOS with corporate certificates:

```bash
# Install certificates from Keychain
security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain > ~/ca-bundle.crt
security find-certificate -a -p /Library/Keychains/System.keychain >> ~/ca-bundle.crt

# Use this bundle
export REQUESTS_CA_BUNDLE=~/ca-bundle.crt
export CURL_CA_BUNDLE=~/ca-bundle.crt

# Then install
./install.sh
```

## Verification Steps

After installation, verify everything works:

```bash
# 1. Check uv installation
uv --version

# 2. Activate environment
source .venv/bin/activate

# 3. Check COS CLI installation
cos --version

# 4. Configure credentials
cos configure

# 5. Test basic operation
cos ls
```

## Alternative: Docker Installation (Future)

If SSL issues persist, consider using Docker (planned for future release):

```bash
# Pull image (when available)
docker pull ghcr.io/sszhu/coscli:latest

# Run
docker run -it --rm \
  -v ~/.cos:/root/.cos \
  ghcr.io/sszhu/coscli:latest cos ls
```

## Common Questions

### Q: Is it safe to disable SSL verification?

**A:** For the installation step (downloading uv), the `-k` flag is only used as a fallback when regular installation fails. The downloaded script is from the official Astral source.

For COS API calls, we disable verification because:
1. Corporate SSL inspection creates "man-in-the-middle" that breaks standard verification
2. We're still using HTTPS (encrypted)
3. Authentication is via secret keys (not relying on SSL for identity)

If this is a concern for your organization, you should:
- Install corporate CA certificates properly
- Use the `REQUESTS_CA_BUNDLE` environment variable
- Work with your IT team to whitelist Tencent Cloud domains

### Q: Why does this happen?

Corporate networks often use SSL inspection proxies that intercept HTTPS traffic. This creates a new SSL certificate signed by the company's CA, which isn't in the standard certificate trust store.

### Q: Can I configure COS CLI to use my company's CA certificates?

Yes! Set environment variables before running:

```bash
export REQUESTS_CA_BUNDLE=/path/to/company-ca.crt
export CURL_CA_BUNDLE=/path/to/company-ca.crt
```

Add these to your `~/.bashrc` or `~/.zshrc` to make them permanent.

## Quick Reference

### Installation Failed - Try These in Order:

1. ✅ Pull latest code: `git pull origin main`
2. ✅ Run updated install script: `./install.sh`
3. ✅ Manual with insecure: `curl -LsSfk https://astral.sh/uv/install.sh | sh`
4. ✅ Use system pip: `python3 -m venv .venv && pip install -e .`
5. ✅ Set proxy variables (if applicable)
6. ✅ Contact IT for CA certificates

### Usage Failed - Check These:

1. ✅ Update to latest: `git pull && pip install -e . --force-reinstall`
2. ✅ Verify auth.py has SSL bypass: `grep patched_request cos/auth.py`
3. ✅ Check Python version: `python --version` (need 3.8+)
4. ✅ Reinstall dependencies: `pip install --force-reinstall -e .`

## Still Having Issues?

1. **Check GitHub Issues**: https://github.com/sszhu/coscli/issues
2. **Open a New Issue**: Include:
   - Error message (full traceback)
   - Operating system and version
   - Python version (`python --version`)
   - Installation method tried
   - Whether you're in a corporate network
   
3. **Contact**: sszhu.soft@gmail.com

## Related Documentation

- [Installation Guide](README.md#installation)
- [uv Documentation](https://github.com/astral-sh/uv)
- [SSL/TLS Troubleshooting](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification)

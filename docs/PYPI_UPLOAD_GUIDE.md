# PyPI Upload Guide for Corporate Networks

## Problem

Uploading to PyPI from corporate networks with self-signed SSL certificates causes SSL verification errors.

## Solution

Use the `upload_ssl_bypass.py` helper script that patches SSL verification before twine runs.

### Quick Upload

```bash
# Build the package
python -m build

# Upload with SSL bypass
python upload_ssl_bypass.py upload dist/*
```

### Verbose Mode (for debugging)

```bash
python upload_ssl_bypass.py upload dist/* --verbose
```

### Skip Existing Files

```bash
python upload_ssl_bypass.py upload dist/* --skip-existing
```

## How It Works

The `upload_ssl_bypass.py` script:

1. **Patches SSL at multiple levels**:
   - Environment variables (`REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`)
   - `ssl.SSLContext.wrap_socket()`
   - `ssl._create_default_https_context()`
   - `requests` HTTPAdapter

2. **Disables warnings**:
   - urllib3 InsecureRequestWarning
   - All Python warnings

3. **Runs twine** with the patched environment

## Alternative: Upload from Different Network

If possible, upload from a network without corporate SSL interception:

```bash
# From home/cloud instance
python -m twine upload dist/*
```

## Verify Upload

Check PyPI after upload:
```bash
# View package page
open https://pypi.org/project/tencent-cos-cli/

# Install and test
pip install tencent-cos-cli
cos --version
```

## Version Management

### Bump Version

Edit `cos/__init__.py`:
```python
__version__ = "2.2.0"  # Current version
```

Edit `pyproject.toml`:
```toml
version = "2.2.0"  # Match __init__.py
```

### Rebuild

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build new version
python -m build
```

### Upload New Version

```bash
python upload_ssl_bypass.py upload dist/*
```

## Troubleshooting

### File Already Exists Error

```
HTTPError: 400 Client Error: File already exists
```

**Solution**: Bump the version number and rebuild.

### SSL Certificate Error (even with bypass)

If the bypass script doesn't work:

1. **Check Python version**:
   ```bash
   python --version  # Should be 3.9+
   ```

2. **Try with system Python**:
   ```bash
   /usr/bin/python3 upload_ssl_bypass.py upload dist/*
   ```

3. **Upload via API token**:
   Create `~/.pypirc`:
   ```ini
   [distutils]
   index-servers = pypi

   [pypi]
   username = __token__
   password = pypi-YOUR-API-TOKEN-HERE
   ```

### Permission Denied

```bash
chmod +x upload_ssl_bypass.py
python upload_ssl_bypass.py upload dist/*
```

### Wrong Package Name

Ensure `pyproject.toml` has correct name:
```toml
[project]
name = "tencent-cos-cli"
```

## Best Practices

### 1. Test Before Upload

```bash
# Install locally
pip install -e .

# Run tests
pytest tests/

# Test CLI
cos --help
cos --version
```

### 2. Update Documentation

Before uploading, ensure:
- [ ] `CHANGELOG.md` updated
- [ ] `README.md` current
- [ ] Version bumped in `__init__.py` and `pyproject.toml`
- [ ] Documentation tested

### 3. Tag Release

```bash
# Create git tag
git tag -a v2.0.1 -m "Release version 2.0.1"
git push origin v2.0.1
```

### 4. Create GitHub Release

After successful PyPI upload:
1. Go to https://github.com/sszhu/coscli/releases
2. Create new release from tag
3. Add release notes from CHANGELOG

## Automated Upload Workflow

For CI/CD (when not behind corporate proxy):

```yaml
# .github/workflows/release.yml
name: Upload to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: python -m twine upload dist/*
```

## Security Notes

### API Tokens

Use PyPI API tokens instead of passwords:

1. Go to https://pypi.org/manage/account/token/
2. Create token with scope "Entire account" or specific project
3. Store in `~/.pypirc`:
   ```ini
   [pypi]
   username = __token__
   password = pypi-AgENdGVzdC5weXBpLm9yZy...
   ```

### SSL Bypass Risks

The `upload_ssl_bypass.py` script disables SSL verification:

- ⚠️ **Use only for uploads from trusted networks**
- ⚠️ **Don't use for downloading packages**
- ✅ **OK for internal corporate uploads**
- ✅ **Verify package integrity after upload**

## Support

If issues persist:
- Check PyPI status: https://status.python.org/
- Ask on PyPI Discourse: https://discuss.python.org/c/packaging/
- File issue: https://github.com/pypi/support/issues

## Quick Reference

```bash
# Complete upload workflow
python -m build                              # Build package
python upload_ssl_bypass.py upload dist/*    # Upload to PyPI
pip install tencent-cos-cli             # Test installation
cos --version                                # Verify version
```

## See Also

- [PyPI Help](https://pypi.org/help/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [SSL Troubleshooting Guide](docs/SSL_TROUBLESHOOTING.md)

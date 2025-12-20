# UV Package Manager Guide for COS CLI

## What is uv?

`uv` is an extremely fast Python package installer and resolver written in Rust. It's 10-100x faster than pip and provides better dependency resolution.

**Key Benefits:**
- ⚡ **10-100x faster** than pip
- 🔒 **Better dependency resolution**
- 🎯 **Drop-in replacement** for pip
- 🚀 **Modern Python tooling**

## Installation Methods

### Method 1: Quick Install (Recommended)

```bash
# Run the installation script (installs uv if needed)
./install.sh
```

This script will:
1. Check for Python
2. Install uv if not present
3. Install COS CLI using uv

### Method 2: Install with Virtual Environment

```bash
# Uses uv to create venv and install
./install-uv.sh

# Activate the virtual environment
source .venv/bin/activate

# Now you can use cos
cos --help
```

### Method 3: Manual Installation

```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Then install COS CLI
uv pip install -e .
```

### Method 4: Traditional pip (Still Works)

```bash
# If you prefer pip
pip install -e .
```

## Using uv with COS CLI

### Install Dependencies

```bash
# Install all dependencies
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"
```

### Create Virtual Environment

```bash
# Create a new virtual environment
uv venv

# Activate it
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install the package
uv pip install -e .
```

### Update Dependencies

```bash
# Update all dependencies
uv pip install --upgrade -e .

# Update specific package
uv pip install --upgrade click
```

### Sync Dependencies (Advanced)

```bash
# Install exact versions from lockfile
uv pip sync requirements.txt
```

## Development Workflow

### Setup Development Environment

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black cos/

# Lint code
ruff check cos/

# Type checking
mypy cos/
```

### Quick Commands

```bash
# Install
uv pip install -e .

# Uninstall
uv pip uninstall tencent-cos-cli

# List installed packages
uv pip list

# Show package info
uv pip show tencent-cos-cli

# Freeze dependencies
uv pip freeze > requirements.txt
```

## Configuration Files

### pyproject.toml

The project now uses `pyproject.toml` instead of `setup.py`. This is the modern Python packaging standard.

```toml
[project]
name = "tencent-cos-cli"
version = "1.0.0"
dependencies = [
    "tencentcloud-sdk-python>=3.0.1000",
    "cos-python-sdk-v5>=1.9.30",
    # ... other dependencies
]

[project.scripts]
cos = "cos.cli:main"
```

### Optional Dependencies

Install with development tools:

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"
```

This includes:
- pytest (testing)
- black (formatting)
- ruff (linting)
- mypy (type checking)

## Migration from pip

If you were using pip before:

```bash
# Old way (pip)
pip install -e .

# New way (uv) - same command!
uv pip install -e .
```

**uv is a drop-in replacement!** All `pip` commands work with `uv pip`.

## Troubleshooting

### uv not in PATH

After installing uv:

```bash
source $HOME/.cargo/env
```

Or add to your `~/.bashrc` or `~/.zshrc`:

```bash
export PATH="$HOME/.cargo/bin:$PATH"
```

### Permission Errors

Use virtual environments instead of `--user`:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Slow First Install

The first time uv runs, it needs to build its cache. Subsequent installs will be much faster.

## Performance Comparison

Typical installation times:

| Tool | Time | Speed |
|------|------|-------|
| pip | 30-60s | 1x |
| uv | 3-5s | **10-20x** |

## Why uv?

1. **Speed**: 10-100x faster than pip
2. **Modern**: Uses latest Python packaging standards
3. **Reliable**: Better dependency resolution
4. **Compatible**: Drop-in replacement for pip
5. **Future-proof**: Active development by Astral (makers of ruff)

## Resources

- **uv Documentation**: https://github.com/astral-sh/uv
- **Installation Guide**: https://astral.sh/uv
- **pyproject.toml**: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/

## Quick Reference

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv
uv venv

# Install package
uv pip install -e .

# Install with dev tools
uv pip install -e ".[dev]"

# Update packages
uv pip install --upgrade -e .

# Run tests
pytest

# Format code
black cos/

# Lint code
ruff check cos/
```

---

**Note**: The project now uses `pyproject.toml` (modern standard) instead of `setup.py` (legacy). Both pip and uv work with this configuration.

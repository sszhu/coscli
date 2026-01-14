# COS CLI

**Modern command-line interface for Tencent Cloud Object Storage**

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![uv](https://img.shields.io/badge/managed%20by-uv-purple.svg)](https://github.com/astral-sh/uv)

A fast, intuitive CLI tool for managing Tencent Cloud Object Storage, built with modern Python tooling.

## ⚡ Quick Start

```bash
# Install from PyPI (recommended)
pip install tencent-cos-cli

# Or install from source
./install.sh
source .venv/bin/activate

# Configure credentials
cos configure

# Use it!
cos ls
cos cp file.txt cos://bucket/
```

## 📁 Project Structure

```
coscli/
├── README.md              # This file
├── CHANGELOG.md           # Version history
├── pyproject.toml         # Modern Python config
├── install.sh             # Installation script
├── .gitignore            
│
├── cos/                   # Main package
│   ├── cli.py            # CLI controller
│   ├── config.py         # Configuration
│   ├── auth.py           # Authentication
│   ├── client.py         # COS client wrapper
│   ├── utils.py          # Utilities
│   ├── constants.py      # Constants
│   ├── exceptions.py     # Custom exceptions
│   └── commands/         # Command modules
│       ├── configure.py  # Setup
│       ├── ls.py        # List
│       ├── cp.py        # Copy
│       ├── rm.py        # Remove
│       ├── mb.py        # Make bucket
│       └── rb.py        # Remove bucket
│
├── docs/                 # Documentation
│   ├── README.md        # Docs index
│   ├── QUICK_REFERENCE.md
│   ├── UV_GUIDE.md
│   └── ...
│
└── tests/               # Test suite
    ├── test_config.py
    └── test_utils.py
```

## 📖 Documentation

- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Common commands
- **[Full Documentation](docs/README.md)** - Complete docs
- **[Development Plan](docs/COS_CLI_DEVELOPMENT_PLAN.md)** - Roadmap

## 🚀 Features

- ✨ **Modern**: Published on PyPI, uses uv for fast development
- 🎯 **Simple**: AWS CLI-like syntax, 14 powerful commands
- 🔐 **Secure**: STS credentials, pre-signed URLs, IAM policies
- 🎨 **Beautiful**: Rich progress bars, colored output
- 📦 **Complete**: Upload, download, sync, bucket management
- ⚙️ **Flexible**: Pattern matching, checksums, multiple profiles
- 🚀 **Advanced**: Lifecycle, CORS, versioning, policy management

## 📦 Commands

| Command | Description |
|---------|-------------|
| `cos configure` | Setup credentials |
| `cos ls` | List buckets/objects |
| `cos cp` | Copy files (with --include/--exclude) |
| `cos mv` | Move/rename objects |
| `cos sync` | Synchronize directories (with --checksum) |
| `cos rm` | Remove objects |
| `cos mb` | Create bucket |
| `cos rb` | Remove bucket |
| `cos presign` | Generate pre-signed URLs |
| `cos token` | Generate temporary credentials |
| `cos lifecycle` | Manage lifecycle policies |
| `cos policy` | Manage bucket policies |
| `cos cors` | Configure CORS |
| `cos versioning` | Manage versioning |

## 🛠️ Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black cos/

# Lint
ruff check cos/
```

## 📝 Version

Current version: **2.2.1**

See [CHANGELOG.md](CHANGELOG.md) for details.

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Credits

- [uv](https://github.com/astral-sh/uv) - Ultra-fast package manager
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Tencent Cloud SDK](https://cloud.tencent.com/document/sdk/Python) - Official SDK

---

**Author**: Shanshan Zhu  
**Email**: sszhu.soft@gmail.com

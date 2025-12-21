# 🎉 Tencent COS CLI v2.0.1 - Initial Public Release

**Release Date**: December 21, 2025  
**Package Name**: `tencent-cos-cli`  
**PyPI**: https://pypi.org/project/tencent-cos-cli/

---

## 🌟 Welcome to Tencent COS CLI!

We're excited to announce the first public release of Tencent COS CLI - a powerful, easy-to-use command-line tool for managing Tencent Cloud Object Storage.

### Why Tencent COS CLI?

- ✅ **Simple & Intuitive**: Familiar commands like `cp`, `sync`, `ls` that work just like you expect
- ✅ **Feature-Rich**: 14 commands covering everything from basic operations to advanced bucket management
- ✅ **Production-Ready**: 169 tests with 100% pass rate
- ✅ **Well-Documented**: Comprehensive guides, examples, and references
- ✅ **Active Development**: Built with modern Python practices and continuously improved

---

## 🚀 Key Features

### Basic Operations
- **File Transfer**: Upload, download, and copy objects with `cp` command
- **Directory Sync**: Intelligent synchronization with `sync` command
- **Object Management**: List, move, and remove objects
- **Bucket Management**: Create, list, and remove buckets

### Advanced Features
- **Lifecycle Policies**: Automate object transitions and expiration rules
- **Access Policies**: Fine-grained IAM-based bucket permissions
- **CORS Configuration**: Configure cross-origin resource sharing
- **Versioning**: Enable object versioning for data protection
- **Pre-signed URLs**: Generate temporary access URLs with `presign`
- **Temporary Credentials**: Generate STS tokens for secure, time-limited access

### Smart Transfer Features
- **Pattern Matching**: Filter files with `--include` and `--exclude` patterns
- **Checksum Verification**: MD5-based integrity checking with `--checksum` flag
- **Bandwidth Throttling**: Control transfer speeds to manage network usage
- **Resume Capability**: Automatically resume interrupted transfers
- **Recursive Operations**: Process entire directory trees efficiently

---

## 📦 Installation

### Easy Installation from PyPI

```bash
pip install tencent-cos-cli
```

### Verify Installation

```bash
cos --version
# Output: cos version 2.0.1

cos --help
# See all available commands
```

### Requirements

- Python 3.8 or higher
- Tencent Cloud COS account with access credentials

---

## 🎯 Complete Command Reference

Tencent COS CLI provides 14 powerful commands:

### Core Commands
- **`configure`** - Set up your COS credentials and default settings
- **`ls`** - List buckets or objects in a bucket
- **`cp`** - Copy files between local and COS, or between COS locations
- **`mv`** - Move or rename objects in COS
- **`sync`** - Synchronize directories between local and COS
- **`rm`** - Remove objects or empty buckets

### Bucket Management
- **`mb`** - Create a new bucket
- **`rb`** - Remove an empty bucket
- **`lifecycle`** - Manage bucket lifecycle policies
- **`policy`** - Manage bucket access policies
- **`cors`** - Configure CORS rules
- **`versioning`** - Enable or suspend object versioning

### Security & Access
- **`presign`** - Generate pre-signed URLs for temporary object access
- **`token`** - Generate temporary STS credentials for delegated access

---

## 📚 Usage Examples

### Getting Started

```bash
# Configure your credentials
cos configure
# Follow the prompts to enter your SecretId, SecretKey, Region, and Bucket

# List all buckets
cos ls

# List objects in a bucket
cos ls cos://mybucket/
```

### File Operations

```bash
# Upload a file
cos cp document.pdf cos://mybucket/

# Upload with custom path
cos cp photo.jpg cos://mybucket/photos/2025/

# Download a file
cos cp cos://mybucket/document.pdf ./

# Copy between COS locations
cos cp cos://bucket1/file.txt cos://bucket2/backup/

# Move/rename object
cos mv cos://mybucket/old-name.txt cos://mybucket/new-name.txt
```

### Directory Operations

```bash
# Upload directory recursively
cos cp ./my-project/ cos://mybucket/projects/ -r

# Download directory
cos cp cos://mybucket/projects/ ./local-backup/ -r

# Sync local to COS (upload only changed files)
cos sync ./website/ cos://mybucket/www/

# Sync with pattern filtering
cos sync ./src/ cos://mybucket/source/ --include "*.py" --exclude "test_*"

# Sync with checksum verification
cos sync ./data/ cos://mybucket/data/ --checksum
```

### Advanced Features

```bash
# Generate pre-signed URL (valid for 1 hour)
cos presign cos://mybucket/private-file.pdf --expires 3600

# Generate temporary credentials (valid for 30 minutes)
cos token --duration 1800 --output env > temp_creds.sh
source temp_creds.sh

# Enable versioning
cos versioning enable cos://mybucket

# Set lifecycle policy
cos lifecycle put cos://mybucket --config lifecycle.json

# Configure CORS
cos cors put cos://mybucket --config cors.json

# Set bucket policy
cos policy put cos://mybucket --policy policy.json
```

### Pattern Matching Examples

```bash
# Upload only Python files
cos cp ./project/ cos://mybucket/ -r --include "*.py"

# Upload all files except tests
cos cp ./src/ cos://mybucket/src/ -r --exclude "test_*" --exclude "*.pyc"

# Multiple patterns
cos sync ./docs/ cos://mybucket/docs/ \
  --include "*.md" \
  --include "*.rst" \
  --exclude "draft_*"
```

---

## 💡 Use Cases

Perfect for:
- **DevOps & CI/CD**: Automate deployments and backups in your pipelines
- **Data Engineers**: Manage large datasets and data lake operations
- **Web Developers**: Deploy static websites and manage assets
- **System Administrators**: Backup and restore operations
- **Data Scientists**: Upload/download training data and model artifacts

---

## 🔒 Security Features

- **Secure Credential Storage**: Encrypted credential management
- **Temporary Credentials**: STS token support for time-limited access
- **Pre-signed URLs**: Share files without exposing credentials
- **IAM Policies**: Fine-grained access control at bucket level
- **Environment Variables**: Support for CI/CD credential injection

---

## 📖 Documentation

Comprehensive documentation to get you started:

- **[README](../README.md)** - Complete user guide with detailed examples
- **[Quick Reference](../QUICK_REFERENCE.md)** - Command cheat sheet for quick lookup
- **[Token Usage Guide](TOKEN_USAGE_GUIDE.md)** - Credential management for CI/CD and automation
- **[Data Backup Guide](DATA_BACKUP_README.md)** - Backup/restore utilities and best practices
- **[Changelog](../CHANGELOG.md)** - Full version history and updates

---

## ✅ Quality & Testing

- **169 comprehensive tests** with 100% pass rate
- Full coverage of all commands and utilities
- Integration tests with live Tencent COS service
- Continuous testing across Python 3.8, 3.9, 3.10, 3.11, 3.12

---

## 🛠️ What's Included

### Production-Ready Features
✅ All core file operations (cp, mv, sync, rm, ls)  
✅ Bucket management (mb, rb)  
✅ Advanced bucket configuration (lifecycle, policy, CORS, versioning)  
✅ Security features (presign, token generation)  
✅ Pattern matching and filtering  
✅ Checksum verification for data integrity  
✅ Resume capability for large transfers  
✅ Comprehensive error handling and logging  

### Developer Experience
✅ Clean, intuitive CLI interface  
✅ Helpful error messages and suggestions  
✅ Progress bars for long operations  
✅ Colorized output for better readability  
✅ Extensive inline help with `--help` flag  
✅ Configuration validation and testing  

---

## 🗺️ Roadmap

We're actively developing new features. Upcoming additions:
- Multi-part upload optimization
- Bucket tagging support
- Inventory reports
- Object metadata management
- Batch operations
- Integration with other Tencent Cloud services

Your feedback and contributions are welcome!

---

## 📝 Version History

### v2.0.1 (2025-12-21) - Initial Public Release
- **First PyPI release** - Now installable with `pip install tencent-cos-cli`
- Complete feature set with 14 commands
- 169 comprehensive tests (100% passing)
- Production-ready with advanced features
- Full documentation and guides

---

## 🤝 Community & Support

### Getting Help
- 📖 Check the [documentation](../README.md) first
- 💬 Ask questions in [GitHub Discussions](https://github.com/sszhu/coscli/discussions)
- 🐛 Report bugs in [GitHub Issues](https://github.com/sszhu/coscli/issues)

### Contributing
We welcome contributions! Whether it's:
- 🐛 Bug reports and fixes
- ✨ New feature suggestions and implementations
- 📖 Documentation improvements
- 🧪 Additional tests
- 💡 Usage examples

**How to contribute:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new features
4. Ensure all tests pass (`pytest`)
5. Submit a pull request

### Bug Reports
Found a bug? Please [open an issue](https://github.com/sszhu/coscli/issues) with:
- Command that failed and full command line used
- Complete error message and stack trace
- Expected vs actual behavior
- Environment details:
  - COS CLI version (`cos --version`)
  - Python version (`python --version`)
  - Operating system

---

## ⚡ Performance

Designed for efficiency:
- Fast parallel uploads/downloads
- Intelligent sync with change detection
- Minimal API calls through smart caching
- Bandwidth throttling to prevent network saturation
- Resume capability for large files

---

## 🙏 Acknowledgments

This project builds on the excellent work of:
- Tencent Cloud COS Python SDK team
- The Python open source community
- Early testers and feedback providers

Special thanks to everyone who contributed ideas, reported issues, and helped shape this tool!

---

## 📄 License

MIT License - Free for personal and commercial use. See [LICENSE](../LICENSE) file for details.

---

## 🔗 Important Links

- 📦 **PyPI Package**: https://pypi.org/project/tencent-cos-cli/
- 💻 **GitHub Repository**: https://github.com/sszhu/coscli
- 🐛 **Issue Tracker**: https://github.com/sszhu/coscli/issues
- 💬 **Discussions**: https://github.com/sszhu/coscli/discussions
- 📘 **Tencent COS Documentation**: https://cloud.tencent.com/document/product/436

---

## 🎯 Get Started Today!

```bash
# Install
pip install tencent-cos-cli

# Configure
cos configure

# Start using it!
cos ls
cos cp myfile.txt cos://mybucket/
```

**Welcome to the Tencent COS CLI community! We're excited to see what you build! 🚀**

---

*Questions? Feedback? We'd love to hear from you! Open an issue or start a discussion on GitHub.*

# Contributing to COS CLI

Thank you for your interest in contributing to COS CLI! We welcome contributions from the community.

## 🎯 Code of Conduct

This project follows a simple code of conduct: be respectful, be constructive, and help make this tool better for everyone.

## 🚀 Quick Start

### Setting Up Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/sszhu/coscli.git
   cd coscli
   ```

2. **Install Development Dependencies**
   ```bash
   # Install uv if you don't have it
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create virtual environment and install
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev]" --native-tls
   ```

3. **Verify Installation**
   ```bash
   cos --version
   python -m pytest tests/
   ```

## 🔧 Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write clear, readable code
- Follow existing code style
- Add docstrings for new functions
- Update type hints where applicable

### 3. Add Tests

All new features and bug fixes should include tests:

```bash
# Add tests in tests/ directory
# Run tests locally
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_your_feature.py -v
```

### 4. Update Documentation

- Update README.md if adding new features
- Add examples to QUICK_REFERENCE.md
- Update CHANGELOG.md with your changes
- Add docstrings to new functions/classes

### 5. Run Quality Checks

```bash
# Run all tests
python tests/run_all_tests.py

# Format code (optional)
black cos/ tests/

# Check linting (optional)
ruff check cos/
```

## 📝 Commit Guidelines

### Commit Message Format

```
type(scope): brief description

Longer explanation if needed

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

**Examples:**
```
feat(sync): add checksum verification with --checksum flag

Add MD5 checksum comparison to sync command to ensure file
integrity during synchronization.

Fixes #45
```

```
fix(cp): handle special characters in object keys

Properly encode object keys containing spaces and special
characters to prevent upload failures.

Fixes #67
```

## 🐛 Reporting Bugs

### Before Submitting

1. Check existing [Issues](https://github.com/sszhu/coscli/issues)
2. Try with the latest version
3. Reproduce with minimal example

### Bug Report Template

```markdown
**Description**
Clear description of the bug

**To Reproduce**
1. Run command: `cos ...`
2. See error

**Expected Behavior**
What should happen

**Environment**
- COS CLI version: `cos --version`
- Python version: `python --version`
- OS: [e.g., Ubuntu 22.04]

**Additional Context**
Any other relevant information
```

## 💡 Suggesting Features

We welcome feature suggestions! Please:

1. Check if already requested in [Issues](https://github.com/sszhu/coscli/issues)
2. Describe the use case clearly
3. Explain why it would be useful
4. Consider implementation complexity

### Feature Request Template

```markdown
**Problem**
What problem does this solve?

**Proposed Solution**
How should it work?

**Alternatives Considered**
Other approaches you thought about

**Use Case**
Example of how you'd use it
```

## 🔍 Code Review Process

1. **Automated Checks**
   - All tests must pass
   - Code should follow project style
   - No merge conflicts

2. **Manual Review**
   - Code is clear and maintainable
   - Tests cover new functionality
   - Documentation is updated
   - Changes are backwards compatible (if possible)

3. **Approval and Merge**
   - Maintainer approval required
   - Squash merge for clean history

## 📦 Project Structure

```
coscli/
├── cos/                    # Main package
│   ├── commands/           # Command implementations
│   ├── cli.py             # CLI entry point
│   ├── config.py          # Configuration management
│   ├── auth.py            # Authentication
│   ├── client.py          # COS client wrapper
│   └── utils.py           # Utility functions
├── tests/                  # Test suite
│   ├── test_*.py          # Test files
│   └── run_all_tests.py   # Test runner
├── docs/                   # Documentation
└── ui/                     # Web UI (experimental)
```

## 🧪 Testing Guidelines

### Test Types

1. **Unit Tests** - Test individual functions
   ```python
   def test_parse_cos_uri():
       bucket, key = parse_cos_uri("cos://bucket/key")
       assert bucket == "bucket"
       assert key == "key"
   ```

2. **Integration Tests** - Test real COS operations
   ```python
   def test_upload_file(cos_client, temp_file):
       cos_client.upload_file(temp_file, "cos://bucket/test.txt")
       assert cos_client.object_exists("cos://bucket/test.txt")
   ```

3. **Mock Tests** - Test without real COS
   ```python
   @patch('cos.client.COSClient')
   def test_command(mock_client):
       # Test command logic without COS
   ```

### Test Coverage

- Aim for >80% coverage for new code
- All bug fixes should include regression tests
- Test both success and error paths

## 🎨 Code Style

### Python Style

- Follow PEP 8
- Use type hints where helpful
- Docstrings for public functions
- Maximum line length: 100 characters

### Example

```python
def upload_file(
    client: COSClient,
    local_path: str,
    cos_uri: str,
    *,
    metadata: Optional[Dict[str, str]] = None
) -> None:
    """Upload a file to COS.
    
    Args:
        client: Authenticated COS client
        local_path: Path to local file
        cos_uri: Destination COS URI (cos://bucket/key)
        metadata: Optional metadata dict
        
    Raises:
        FileNotFoundError: If local file doesn't exist
        COSError: If upload fails
    """
    # Implementation
```

## 📚 Documentation

### Types of Documentation

1. **Code Comments** - Explain complex logic
2. **Docstrings** - Document functions/classes
3. **README.md** - User guide and examples
4. **QUICK_REFERENCE.md** - Command cheat sheet
5. **docs/** - Detailed guides

### Documentation Style

- Clear and concise
- Include examples
- Explain the "why" not just the "what"
- Keep examples up-to-date

## 🏷️ Release Process

Maintainers only:

1. Update version in `pyproject.toml` and `cos/__init__.py`
2. Update `CHANGELOG.md`
3. Create release notes
4. Tag release: `git tag v2.0.0`
5. Build: `uv build`
6. Publish to PyPI: `uv publish`
7. Create GitHub release

## 🤝 Getting Help

- **Questions**: Open a [Discussion](https://github.com/sszhu/coscli/discussions)
- **Bugs**: Open an [Issue](https://github.com/sszhu/coscli/issues)
- **Security**: Email maintainer directly

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Recognition

Contributors will be:
- Listed in release notes
- Credited in CHANGELOG.md
- Appreciated by the community!

Thank you for contributing to COS CLI! 🎉

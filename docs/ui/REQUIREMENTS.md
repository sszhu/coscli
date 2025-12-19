# COS Data Manager UI - Requirements

## Python Dependencies

### Core Dependencies
streamlit>=1.28.0          # Web UI framework
qcloud-cos>=5.9.0          # Tencent COS SDK (already installed)

### Testing Dependencies
pytest>=7.4.0              # Unit testing framework
pytest-mock>=3.11.0        # Mocking for tests
pytest-cov>=4.1.0          # Coverage reporting

### Optional Dependencies
pandas>=2.0.0              # CSV preview (optional)
pillow>=10.0.0             # Image preview (optional)

## Installation

### Option 1: Install in existing environment
```bash
pip install streamlit pytest pytest-mock pytest-cov
```

### Option 2: Create new virtual environment
```bash
python3 -m venv venv_ui
source venv_ui/bin/activate
pip install streamlit pytest pytest-mock pytest-cov
```

### Option 3: Use conda/micromamba
```bash
micromamba create -n cos-ui python=3.9 streamlit pytest pytest-mock -y
micromamba activate cos-ui
```

## Verify Installation

```bash
# Check streamlit
streamlit --version

# Check pytest
pytest --version

# Check COS CLI (should already be installed)
python -m cos --version
```

## Running the UI

```bash
# From the coscli directory
streamlit run ui/app.py
```

The UI will open at http://localhost:8501

## Running Tests

```bash
# Run all UI tests
pytest tests/ui/ -v

# Run with coverage
pytest tests/ui/ --cov=ui.src --cov-report=html

# Run specific test file
pytest tests/ui/test_cos_client_wrapper.py -v
```

## System Requirements

- Python 3.8 or higher
- 2GB RAM minimum
- Network access to Tencent Cloud COS endpoints
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Port Configuration

By default, Streamlit uses port 8501. To use a different port:

```bash
streamlit run ui/app.py --server.port 8080
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install streamlit
```

### "ModuleNotFoundError: No module named 'pytest'"
```bash
pip install pytest pytest-mock
```

### Port already in use
```bash
# Kill existing streamlit process
pkill -f streamlit

# Or use a different port
streamlit run ui/app.py --server.port 8502
```

### Virtual environment issues
If the .venv doesn't have pip, recreate it:
```bash
rm -rf .venv
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install streamlit pytest pytest-mock
```

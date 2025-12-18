# COS Data Manager UI - Implementation Guide

## Overview

This document provides a complete guide for implementing and running the COS Data Manager web UI, a modern interface for Tencent Cloud Object Storage designed by sszhu.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Development Guide](#development-guide)
7. [Design Documentation](#design-documentation)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- COS CLI installed and configured
- Streamlit package

### Install and Run
```bash
# Install Streamlit
pip install streamlit

# Run the UI
streamlit run ui_app.py
```

The UI will open in your browser at http://localhost:8501

---

## 🏗️ Architecture

### Project Structure

```
coscli/
├── ui_app.py                      # Main entry point (Home page)
├── UI_DESIGN.md                   # Complete design documentation
├── UI_COMPONENTS.md               # Component breakdown and specs
├── README_UI.md                   # This file
│
├── ui/                            # UI application directory
│   ├── pages/                     # Multi-page Streamlit pages
│   │   ├── file_manager.py        # File browsing and management
│   │   ├── buckets.py             # Bucket management (TODO)
│   │   ├── transfers.py           # Batch operations (TODO)
│   │   └── settings.py            # Configuration (TODO)
│   │
│   ├── components/                # Reusable UI components
│   │   ├── layout/                # Layout components
│   │   ├── navigation/            # Navigation components
│   │   ├── data_display/          # Data display components
│   │   ├── input/                 # Input components
│   │   ├── feedback/              # Feedback components
│   │   └── actions/               # Action components
│   │
│   ├── src/                       # Core utilities
│   │   ├── config.py              # Configuration constants
│   │   ├── utils.py               # Utility functions
│   │   └── cos_client.py          # COS client wrapper (TODO)
│   │
│   └── static/                    # Static assets
│       ├── styles/                # CSS styles
│       │   └── page.css           # Custom CSS
│       └── logos/                 # Logo images
│           └── tencent-logo.svg   # Tencent branding
│
└── cos/                           # Existing COS CLI (unchanged)
    ├── cli.py
    ├── client.py
    ├── config.py
    └── ...
```

---

## 💿 Installation

### Option 1: Use Existing Environment

If you already have the COS CLI installed:

```bash
# Install Streamlit
pip install streamlit

# That's it! The UI reuses the existing COS CLI code
```

### Option 2: Fresh Installation

```bash
# Clone/navigate to coscli directory
cd /path/to/coscli

# Install COS CLI and UI dependencies
pip install -e .
pip install streamlit

# Configure COS credentials (if not already done)
cos configure
```

---

## ⚙️ Configuration

### COS Credentials

The UI uses the same credentials as the CLI. Configure them using:

```bash
cos configure
```

This creates `~/.cos/config.json` with your credentials.

### Environment Variables (Optional)

Create a `.streamlit/secrets.toml` file for UI-specific settings:

```toml
# COS Configuration
[cos]
default_bucket = "my-bucket"
default_region = "ap-shanghai"
default_profile = "default"

# UI Configuration
[ui]
page_size = 50
max_upload_size_mb = 5000
debug_mode = false
```

---

## 🎮 Running the Application

### Development Mode

```bash
# Run with auto-reload
streamlit run ui_app.py

# Run on specific port
streamlit run ui_app.py --server.port 8502

# Run with debug mode
streamlit run ui_app.py --logger.level=debug
```

### Production Mode

```bash
# Run in production (no auto-reload)
streamlit run ui_app.py --server.headless true
```

### Docker Deployment (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install -e . && pip install streamlit

# Copy application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "ui_app.py", "--server.headless", "true", "--server.address", "0.0.0.0"]
```

Build and run:

```bash
docker build -t cos-ui .
docker run -p 8501:8501 -v ~/.cos:/root/.cos cos-ui
```

---

## 👨‍💻 Development Guide

### Adding a New Page

1. Create file in `ui/pages/`:

```python
# ui/pages/my_page.py
import streamlit as st
from ui.src.utils import render_sidebar_navigation, inject_global_styles

st.set_page_config(page_title="My Page", layout="wide")
inject_global_styles()
render_sidebar_navigation(current_page="my_page")

st.title("🎯 My Page")
# Your page content here
```

2. Add navigation link in `ui/src/utils.py`:

```python
def render_sidebar_navigation(current_page: str = "home"):
    # ... existing code ...
    pages = [
        # ... existing pages ...
        ("ui/pages/my_page.py", "🎯 My Page", "my_page"),
    ]
```

### Creating a Component

Follow the component specifications in `UI_COMPONENTS.md`:

```python
# ui/components/my_component.py
import streamlit as st
from typing import Optional

def render_my_component(
    title: str,
    data: list,
    on_action: Optional[callable] = None
) -> None:
    """
    Render my custom component.
    
    Args:
        title: Component title
        data: Data to display
        on_action: Optional callback
    """
    st.markdown(f"### {title}")
    
    # Component implementation
    for item in data:
        if st.button(item):
            if on_action:
                on_action(item)
```

### Styling

Add custom styles in `ui/static/styles/page.css`:

```css
/* Custom component styles */
.my-component {
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
```

Load styles in your page:

```python
from ui.src.utils import inject_global_styles
inject_global_styles()
```

---

## 📚 Design Documentation

### Complete Design Specification

See **[UI_DESIGN.md](UI_DESIGN.md)** for:
- High-level UI layout
- Page-by-page wireframes
- Design tokens (colors, typography, spacing)
- Interaction patterns
- Accessibility guidelines
- ASCII wireframes

### Component Library

See **[UI_COMPONENTS.md](UI_COMPONENTS.md)** for:
- Detailed component specifications
- API documentation
- Usage examples
- Code snippets
- Testing strategies

---

## 🎨 Design System

### Color Palette (Tencent Blue Theme)

```python
COLORS = {
    'primary': '#006EFF',           # Tencent Blue
    'primary_dark': '#0052CC',
    'primary_light': '#4D9FFF',
    'success': '#52C41A',
    'warning': '#FFB84D',
    'danger': '#FF4D4F',
    'text': '#1A1A1A',
    'background': '#F5F5F5',
}
```

### Typography

- **Font**: System default (Inter, Helvetica Neue, sans-serif)
- **Sizes**: 12px (caption) → 16px (body) → 32px (h1)
- **Weights**: 400 (normal), 600 (semibold), 700 (bold)

### Spacing

- XS: 4px
- SM: 8px
- MD: 16px
- LG: 24px
- XL: 32px

---

## 🔧 Troubleshooting

### Issue: "COS client not initialized"

**Solution**: Configure credentials first

```bash
cos configure
```

Then restart the UI.

### Issue: "Module not found: cos"

**Solution**: Install COS CLI in editable mode

```bash
pip install -e .
```

### Issue: Streamlit not found

**Solution**: Install Streamlit

```bash
pip install streamlit
```

### Issue: Styles not applying

**Solution**: Create the CSS file

```bash
mkdir -p ui/static/styles
touch ui/static/styles/page.css
```

Then add styles from `UI_DESIGN.md` Section 5.4.

### Issue: "Page not found" when navigating

**Solution**: Ensure file paths in `st.page_link()` match actual file locations

```python
# Correct path (from project root)
st.page_link("ui/pages/file_manager.py", label="Files")

# Not this
st.page_link("pages/file_manager.py", label="Files")
```

---

## 🚧 Implementation Status

### ✅ Completed
- [x] Project structure
- [x] Main app (Home page)
- [x] File Manager page (basic)
- [x] Configuration module
- [x] Utility functions
- [x] Sidebar navigation
- [x] Custom CSS styles
- [x] Design documentation

### 🚧 In Progress
- [ ] File Manager (complete implementation)
  - [ ] Folder tree view
  - [ ] File download
  - [ ] File deletion
  - [ ] File preview
- [ ] Buckets page
- [ ] Transfers page
- [ ] Settings page

### 📋 To Do
- [ ] Complete component library
- [ ] Error handling improvements
- [ ] Progress tracking for uploads
- [ ] Batch operations
- [ ] File search and filtering
- [ ] Storage analytics
- [ ] User authentication (if needed)
- [ ] Unit tests
- [ ] Integration tests
- [ ] User documentation
- [ ] Video tutorials

---

## 📈 Development Roadmap

### Phase 1: Foundation (Weeks 1-2) ✅
- [x] Set up project structure
- [x] Create base layout and navigation
- [x] Implement configuration and utilities
- [x] Design documentation

### Phase 2: File Manager (Weeks 3-4)
- [ ] Complete file list view
- [ ] Add folder tree navigation
- [ ] Implement upload panel
- [ ] Add download functionality
- [ ] Implement search and filtering

### Phase 3: Bucket Management (Week 5)
- [ ] Bucket list view
- [ ] Bucket creation wizard
- [ ] Bucket configuration UI

### Phase 4: Batch Operations (Weeks 6-7)
- [ ] Batch upload UI
- [ ] Batch download UI
- [ ] Sync functionality
- [ ] Progress tracking

### Phase 5: Polish & Testing (Week 8)
- [ ] Settings page
- [ ] Error handling improvements
- [ ] Performance optimization
- [ ] User testing and feedback

---

## 🤝 Contributing

### Coding Standards

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Document functions with docstrings
- Keep components modular and reusable

### Component Guidelines

- Components should be self-contained
- Use session state for component-level state
- Provide clear props/arguments
- Include usage examples in docstrings

### Testing

```bash
# Run tests (when implemented)
pytest tests/

# Run specific test file
pytest tests/test_components/test_file_list.py
```

---

## 📞 Support

### Documentation
- [COS CLI Documentation](docs/README.md)
- [UI Design Specification](UI_DESIGN.md)
- [Component Library](UI_COMPONENTS.md)

### Getting Help
- Check troubleshooting section above
- Review design documentation
- Check Streamlit documentation: https://docs.streamlit.io

---

## 📄 License

Same license as COS CLI (MIT)

---

## 🙏 Acknowledgments

- **Design Inspiration**: AutoLEAD UI (Sanofi)
- **Framework**: Streamlit
- **Cloud Provider**: Tencent Cloud COS

---

## 📝 Changelog

### Version 1.0.0 (2024-12-18)
- Initial UI implementation
- Home dashboard
- Basic file manager
- Configuration and utilities
- Complete design documentation

---

**Last Updated**: December 18, 2025  
**Version**: 1.0.0  
**Status**: Alpha (Development)

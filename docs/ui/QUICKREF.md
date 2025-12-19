# COS UI - Quick Reference Guide

Quick reference for developers working on the COS Data Manager UI.

---

## 📦 Installation & Setup

```bash
# Install dependencies
pip install streamlit

# Configure COS credentials
cos configure

# Run the application
streamlit run ui/app.py
```

---

## 📂 Project Structure

```
ui/
├── src/                   # Core utilities & business logic
│   ├── config.py          # Constants, colors, emojis
│   ├── cos_client_wrapper.py  # WebCOSClient wrapper
│   ├── utils.py           # Helper functions
│   ├── page_utils.py      # Page setup utilities
│   └── file_operations.py # File operations logic
├── pages/                 # Pages only
│   ├── file_manager.py    # File browsing (refactored)
│   ├── buckets.py         # Bucket management
│   ├── transfers.py       # Batch operations
│   └── settings.py        # Configuration
├── components/            # Reusable UI components
│   ├── status_indicators.py
│   ├── progress.py
│   ├── file_display.py
│   ├── action_buttons.py
│   └── widgets.py         # Common widgets
└── static/
    └── styles/
        └── page.css       # Custom CSS
```

---

## 🎨 Design Tokens

```python
# Colors (Tencent Blue theme)
PRIMARY = '#006EFF'
PRIMARY_DARK = '#0052CC'
SUCCESS = '#52C41A'
DANGER = '#FF4D4F'

# Spacing
XS, SM, MD, LG, XL = 4, 8, 16, 24, 32  # px

# Emojis
FILE_EMOJIS = {
    'CSV': '📊', 'JSON': '⚙️', 'TXT': '📝',
    'PNG': '🖼️', 'ZIP': '📦', 'PY': '🐍'
}
```

---

## 🔧 Common Patterns

### Page Template
```python
import streamlit as st
from ui.src.utils import inject_global_styles, render_sidebar_navigation

st.set_page_config(page_title="Page Title", layout="wide")
inject_global_styles()
render_sidebar_navigation(current_page="page_id")

st.title("📄 Page Title")
# Your content here
```

### Session State Initialization
```python
from ui.src.utils import init_session_state

init_session_state({
    'key1': 'default_value',
    'key2': [],
    'key3': {}
})
```

### COS Client Access
```python
from ui.src.utils import get_cos_client

cos_client = get_cos_client()
if cos_client:
    # Use client
    pass
else:
    st.warning("Please configure credentials")
```

### Error Handling
```python
from ui.src.utils import handle_error

try:
    # Your code
    pass
except Exception as e:
    handle_error(e, "Context message")
```

### Formatting
```python
from ui.src.utils import format_size, format_datetime, get_file_emoji

size_str = format_size(1234567)      # "1.2 MB"
date_str = format_datetime(dt)        # "2h ago"
emoji = get_file_emoji("data.csv")    # "📊"
```

---

## 📋 Component Examples

### Metric Card
```python
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Label", "Value", delta="Change")
```

### File List (Phase 2 Enhanced)
```python
# With pagination, sorting, filtering
files = load_files_and_folders(bucket, prefix)

# Filter files
if st.session_state.search_query:
    files = [f for f in files if st.session_state.search_query.lower() in f['name'].lower()]

if st.session_state.filter_type != 'all':
    files = [f for f in files if f['name'].lower().endswith(st.session_state.filter_type)]

# Sort files
if st.session_state.sort_by == 'name':
    files.sort(key=lambda f: f['name'].lower(), reverse=(st.session_state.sort_direction == 'desc'))

# Paginate
page_size = st.session_state.page_size
page_num = st.session_state.page_num
start_idx = (page_num - 1) * page_size
page_files = files[start_idx:start_idx + page_size]

# Display with checkboxes
for file in page_files:
    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
    with col1:
        st.checkbox("", key=f"select_{file['key']}")
    with col2:
        st.write(f"{get_file_emoji(file['name'])} {file['name']}")
    with col3:
        st.caption(format_size(file['size']))
    with col4:
        st.button("⬇️ Download", key=f"dl_{file['key']}")
```

### Upload Panel
```python
uploaded_files = st.file_uploader(
    "Select files",
    accept_multiple_files=True
)

if uploaded_files:
    for file in uploaded_files:
        st.write(f"{file.name} - {format_size(len(file.getvalue()))}")
    
    if st.button("Upload"):
        # Upload logic
        pass
```

### Progress Bar
```python
progress = st.progress(0)
for i in range(100):
    progress.progress((i + 1) / 100)
    time.sleep(0.1)
progress.empty()
```

---

## 🎯 Common Tasks

### Add New Page
1. Create `ui/pages/my_page.py`
2. Add navigation in `ui/src/utils.py`
3. Follow page template above

### Add New Component
1. Create `ui/components/my_component.py`
2. Document API and props
3. Add usage example

### Update Styles
1. Edit `ui/static/styles/page.css`
2. Styles inject automatically

### Add Configuration
1. Update `ui/src/config.py`
2. Import where needed

---

## 🐛 Debugging

### Enable Debug Mode
```python
# In .streamlit/secrets.toml
debug_mode = true
```

### View Session State
```python
st.write(st.session_state)
```

### Check COS Client
```python
cos_client = get_cos_client()
st.write(type(cos_client))
st.write(dir(cos_client))
```

---

## 📚 Key Documentation

- **Design Spec**: `UI_DESIGN.md`
- **Components**: `UI_COMPONENTS.md`
- **Mockups**: `UI_MOCKUPS.md`
- **Full Guide**: `README_UI.md`
- **Summary**: `SUMMARY.md`

---

## 🔗 Useful Links

- [Streamlit Docs](https://docs.streamlit.io)
- [COS API Reference](https://cloud.tencent.com/document/product/436)
- [Tencent Cloud Console](https://console.cloud.tencent.com)

---

## ⚡ Hot Tips

1. **Auto-reload**: Streamlit auto-reloads on file save
2. **Cache**: Use `@st.cache_data` for expensive operations
3. **State**: Store state in `st.session_state`
4. **Debug**: Add `st.write()` everywhere to debug
5. **Emojis**: Use emojis for icons (no dependencies!)

---

**Last Updated**: 2025-12-18

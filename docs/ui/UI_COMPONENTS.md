# COS CLI UI - Component Breakdown & Implementation Guide

## Component Library Structure

This document provides detailed specifications for all reusable components in the COS CLI UI.

---

## Component Hierarchy

```
components/
├── layout/
│   ├── sidebar.py           # Navigation sidebar
│   ├── header.py            # Page header with breadcrumbs
│   └── page_container.py    # Standard page wrapper
├── navigation/
│   ├── tree_view.py         # Folder tree navigation
│   ├── breadcrumbs.py       # Path breadcrumb trail
│   └── pagination.py        # List pagination controls
├── data_display/
│   ├── file_list.py         # File list table
│   ├── file_card.py         # File card view (grid)
│   ├── metric_card.py       # Dashboard metrics
│   └── stats_chart.py       # Usage statistics charts
├── input/
│   ├── search_bar.py        # Real-time search
│   ├── filter_panel.py      # Multi-criteria filters
│   ├── upload_zone.py       # Drag-and-drop upload
│   └── bucket_selector.py   # Bucket dropdown
├── feedback/
│   ├── progress_bar.py      # Upload/download progress
│   ├── toast.py             # Notification toasts
│   ├── loading_spinner.py   # Loading states
│   └── empty_state.py       # No data placeholder
└── actions/
    ├── action_button.py     # Styled buttons
    ├── context_menu.py      # Right-click menu
    └── confirm_modal.py     # Confirmation dialogs
```

---

## Detailed Component Specifications

### 1. Layout Components

#### 1.1 Sidebar Navigation
**File**: `components/layout/sidebar.py`

**Purpose**: Persistent navigation menu with logo and page links

**Props**:
- `current_page` (str): Active page identifier
- `user_name` (str, optional): Display user name
- `show_logo` (bool, default=True): Show/hide logo

**API**:
```python
def render_sidebar(current_page: str, user_name: Optional[str] = None) -> None:
    """
    Render the navigation sidebar.
    
    Args:
        current_page: Current active page ('home', 'files', 'buckets', 'transfers', 'settings')
        user_name: Optional user name to display
    """
```

**Example**:
```python
from components.layout.sidebar import render_sidebar

render_sidebar(current_page="files", user_name="admin")
```

**Design**:
```
┌─────────────────────┐
│ [LOGO]              │
│ COS Manager         │
│                     │
│ 🏠 Dashboard        │
│ 🗂️ Files  *         │ <- Active
│ 🪣 Buckets          │
│ 📤 Transfers        │
│ ⚙️ Settings         │
│                     │
│ ─────────────────── │
│                     │
│ 👤 admin            │
│ 🔓 Logout           │
└─────────────────────┘
```

---

#### 1.2 Page Header
**File**: `components/layout/header.py`

**Purpose**: Consistent page header with title and breadcrumbs

**Props**:
- `title` (str): Page title
- `subtitle` (str, optional): Subtitle/description
- `breadcrumbs` (List[Tuple[str, str]]): Breadcrumb trail [(label, link), ...]
- `actions` (List[dict], optional): Action buttons in header

**API**:
```python
def render_header(
    title: str,
    subtitle: Optional[str] = None,
    breadcrumbs: Optional[List[Tuple[str, str]]] = None,
    actions: Optional[List[dict]] = None
) -> None:
    """Render page header with optional breadcrumbs and actions"""
```

**Example**:
```python
render_header(
    title="🗂️ File Manager",
    subtitle="Browse and manage files in COS buckets",
    breadcrumbs=[
        ("Home", "/"),
        ("Files", "/files"),
        ("my-bucket", "/files/my-bucket")
    ],
    actions=[
        {"label": "Upload", "icon": "📤", "on_click": upload_callback}
    ]
)
```

---

### 2. Navigation Components

#### 2.1 Tree View
**File**: `components/navigation/tree_view.py`

**Purpose**: Hierarchical folder navigation with expand/collapse

**Props**:
- `bucket` (str): Bucket name
- `initial_prefix` (str): Starting prefix
- `on_select` (Callable): Callback when folder selected
- `max_depth` (int, default=5): Maximum tree depth
- `show_file_count` (bool, default=True): Show file counts

**API**:
```python
def render_tree_view(
    bucket: str,
    initial_prefix: str = "",
    on_select: Optional[Callable[[str], None]] = None,
    max_depth: int = 5,
    show_file_count: bool = True
) -> None:
    """Render folder tree navigation"""
```

**State Management**:
```python
# Session state keys
st.session_state.tree_expanded_folders  # Set of expanded folder keys
st.session_state.tree_selected_folder   # Currently selected folder
```

**Example**:
```python
def handle_folder_select(prefix: str):
    st.session_state.current_prefix = prefix
    st.rerun()

render_tree_view(
    bucket="my-bucket",
    initial_prefix="data/",
    on_select=handle_folder_select
)
```

**Design**:
```
📁 Folders
─────────────
▼ data/ (47)
  ▼ experiments/ (23)
    • exp_001/ (12)
    • exp_002/ (8)
    • failed/ (3)
  • raw/ (15)
  • processed/ (9)
▶ archives/ (156)
▶ backups/ (89)
```

---

#### 2.2 Breadcrumbs
**File**: `components/navigation/breadcrumbs.py`

**Purpose**: Show current path with clickable navigation

**Props**:
- `bucket` (str): Current bucket
- `prefix` (str): Current prefix/path
- `on_navigate` (Callable): Navigate callback

**API**:
```python
def render_breadcrumbs(
    bucket: str,
    prefix: str,
    on_navigate: Callable[[str], None]
) -> None:
    """Render breadcrumb navigation"""
```

**Design**:
```
my-bucket / data / experiments / exp_001 /
   ↑        ↑       ↑             ↑
(Clickable to navigate up hierarchy)
```

---

#### 2.3 Pagination
**File**: `components/navigation/pagination.py`

**Purpose**: Paginate large file lists

**Props**:
- `total_items` (int): Total number of items
- `page_size` (int, default=50): Items per page
- `current_page` (int): Current page (1-indexed)
- `on_page_change` (Callable): Page change callback

**API**:
```python
def render_pagination(
    total_items: int,
    page_size: int = 50,
    current_page: int = 1,
    on_page_change: Callable[[int], None] = None
) -> None:
    """Render pagination controls"""
```

**Design**:
```
[← Previous]  Page 3 / 12  [Next →]
Showing 101-150 of 573 files

[1] [2] [3] ... [10] [11] [12]
```

---

### 3. Data Display Components

#### 3.1 File List
**File**: `components/data_display/file_list.py`

**Purpose**: Display files in table format with actions

**Props**:
- `files` (List[Dict]): File metadata list
- `selectable` (bool, default=True): Enable checkboxes
- `sortable` (bool, default=True): Enable column sorting
- `show_actions` (bool, default=True): Show action buttons
- `on_action` (Callable): Action callback

**API**:
```python
def render_file_list(
    files: List[Dict[str, Any]],
    selectable: bool = True,
    sortable: bool = True,
    show_actions: bool = True,
    on_action: Optional[Callable[[str, str], None]] = None
) -> List[str]:
    """
    Render file list table.
    
    Returns:
        List of selected file keys
    """
```

**File Dict Schema**:
```python
{
    'key': 'data/file.csv',           # Full S3 key
    'name': 'file.csv',                # Display name
    'size': 2457600,                   # Bytes
    'last_modified': datetime(...),    # Datetime object
    'etag': '"abc123..."',             # ETag
    'storage_class': 'STANDARD'        # Storage class
}
```

**Example**:
```python
files = cos_client.list_objects(bucket, prefix)
selected = render_file_list(
    files=files,
    on_action=lambda action, key: handle_action(action, key)
)

if selected:
    st.write(f"Selected {len(selected)} files")
```

**Design**:
```
┌──────────────────────────────────────────────────────┐
│ ☑️ Name         │ 📦 Size │ 📅 Modified  │ Actions  │
├──────────────────────────────────────────────────────┤
│ ☑️ 📊 data.csv  │ 2.4 MB  │ 2h ago      │ [⬇️][🗑️]│
│ ☐ 📝 log.txt    │ 120 KB  │ 5h ago      │ [⬇️][🗑️]│
│ ☐ 🖼️ chart.png │ 890 KB  │ 1d ago      │ [⬇️][🗑️]│
└──────────────────────────────────────────────────────┘
```

---

#### 3.2 Metric Card
**File**: `components/data_display/metric_card.py`

**Purpose**: Display key metrics on dashboard

**Props**:
- `label` (str): Metric label
- `value` (str): Primary value
- `delta` (str, optional): Change indicator
- `icon` (str): Emoji icon
- `color` (str, optional): Card accent color

**API**:
```python
def render_metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    icon: str = "📊",
    color: Optional[str] = None
) -> None:
    """Render metric card"""
```

**Example**:
```python
col1, col2, col3 = st.columns(3)
with col1:
    render_metric_card(
        label="Total Files",
        value="1,247",
        delta="+12 today",
        icon="📄"
    )
```

**Design**:
```
┌──────────────┐
│ 📄           │
│ Total Files  │
│              │
│ 1,247        │
│ +12 today    │
└──────────────┘
```

---

### 4. Input Components

#### 4.1 Search Bar
**File**: `components/input/search_bar.py`

**Purpose**: Real-time file search with debouncing

**Props**:
- `placeholder` (str): Placeholder text
- `on_search` (Callable): Search callback
- `debounce_ms` (int, default=300): Debounce delay

**API**:
```python
def render_search_bar(
    placeholder: str = "Search files...",
    on_search: Optional[Callable[[str], None]] = None,
    debounce_ms: int = 300
) -> str:
    """
    Render search bar with debouncing.
    
    Returns:
        Current search query
    """
```

**Example**:
```python
search_query = render_search_bar(
    placeholder="Search by filename...",
    on_search=lambda q: filter_files(q)
)
```

---

#### 4.2 Upload Zone
**File**: `components/input/upload_zone.py`

**Purpose**: Drag-and-drop file upload with preview

**Props**:
- `bucket` (str): Target bucket
- `prefix` (str): Target prefix
- `accept_multiple` (bool, default=True): Multiple files
- `on_upload` (Callable): Upload callback
- `show_preview` (bool, default=True): Show file list

**API**:
```python
def render_upload_zone(
    bucket: str,
    prefix: str,
    accept_multiple: bool = True,
    on_upload: Optional[Callable[[List], None]] = None,
    show_preview: bool = True
) -> None:
    """Render file upload zone"""
```

**Example**:
```python
def handle_upload(files):
    for file in files:
        cos_client.upload_file(file, bucket, prefix + file.name)
    st.success(f"Uploaded {len(files)} files!")

render_upload_zone(
    bucket="my-bucket",
    prefix="uploads/",
    on_upload=handle_upload
)
```

**Design**:
```
┌─────────────────────────────────────┐
│                                     │
│   📤 Drag & Drop Files Here         │
│   or click to browse                │
│                                     │
└─────────────────────────────────────┘

Files ready to upload:
• data.csv (2.4 MB)
• model.pkl (45 MB)

[🚀 Upload 2 files]
```

---

#### 4.3 Filter Panel
**File**: `components/input/filter_panel.py`

**Purpose**: Multi-criteria file filtering

**Props**:
- `available_filters` (Dict): Available filter types
- `on_filter_change` (Callable): Filter callback

**API**:
```python
def render_filter_panel(
    available_filters: Dict[str, List[str]],
    on_filter_change: Optional[Callable[[Dict], None]] = None
) -> Dict[str, List[str]]:
    """
    Render filter panel.
    
    Returns:
        Active filters
    """
```

**Example**:
```python
filters = render_filter_panel(
    available_filters={
        'file_type': ['CSV', 'JSON', 'PNG'],
        'size': ['< 1 MB', '1-10 MB', '> 10 MB'],
        'date': ['Today', 'This week', 'This month']
    },
    on_filter_change=lambda f: apply_filters(f)
)
```

**Design**:
```
┌─────────────────────────┐
│ 🔍 Filters              │
├─────────────────────────┤
│ 📊 File Type            │
│ ☑️ CSV                  │
│ ☐ JSON                  │
│ ☐ PNG                   │
│                         │
│ 📦 Size                 │
│ ☐ < 1 MB                │
│ ☑️ 1-10 MB              │
│ ☐ > 10 MB               │
│                         │
│ [Clear All]             │
└─────────────────────────┘
```

---

### 5. Feedback Components

#### 5.1 Progress Bar
**File**: `components/feedback/progress_bar.py`

**Purpose**: Show upload/download progress with speed

**Props**:
- `total` (int): Total items/bytes
- `current` (int): Current progress
- `label` (str): Progress label
- `show_speed` (bool, default=True): Show transfer speed

**API**:
```python
def render_progress_bar(
    total: int,
    current: int,
    label: str,
    show_speed: bool = True
) -> None:
    """Render progress bar with speed indicator"""
```

**Example**:
```python
render_progress_bar(
    total=100,
    current=65,
    label="Uploading files",
    show_speed=True
)
```

**Design**:
```
Uploading files
████████████░░░░░░░░ 65% (65/100)
Speed: 12.5 MB/s | ETA: 2m 15s
```

---

#### 5.2 Toast Notifications
**File**: `components/feedback/toast.py`

**Purpose**: Non-intrusive success/error messages

**Props**:
- `message` (str): Notification message
- `type` (str): 'success', 'error', 'warning', 'info'
- `duration` (int, default=3000): Display duration (ms)

**API**:
```python
def show_toast(
    message: str,
    type: str = "info",
    duration: int = 3000
) -> None:
    """Show toast notification"""
```

**Example**:
```python
show_toast("File uploaded successfully!", type="success")
show_toast("Connection failed. Retry?", type="error")
```

---

#### 5.3 Empty State
**File**: `components/feedback/empty_state.py`

**Purpose**: Friendly placeholder when no data

**Props**:
- `icon` (str): Emoji icon
- `title` (str): Primary message
- `description` (str): Supporting text
- `action` (dict, optional): CTA button

**API**:
```python
def render_empty_state(
    icon: str,
    title: str,
    description: str,
    action: Optional[Dict[str, Any]] = None
) -> None:
    """Render empty state placeholder"""
```

**Example**:
```python
render_empty_state(
    icon="📭",
    title="No files found",
    description="Upload files to get started",
    action={
        "label": "Upload Files",
        "on_click": open_upload_panel
    }
)
```

**Design**:
```
┌─────────────────────────┐
│                         │
│         📭              │
│                         │
│    No files found       │
│                         │
│ Upload files to get     │
│    started              │
│                         │
│   [Upload Files]        │
│                         │
└─────────────────────────┘
```

---

### 6. Action Components

#### 6.1 Action Button
**File**: `components/actions/action_button.py`

**Purpose**: Styled, accessible buttons

**Props**:
- `label` (str): Button text
- `icon` (str, optional): Emoji icon
- `type` (str): 'primary', 'secondary', 'danger'
- `on_click` (Callable): Click handler
- `disabled` (bool, default=False): Disabled state

**API**:
```python
def render_action_button(
    label: str,
    icon: Optional[str] = None,
    type: str = "secondary",
    on_click: Optional[Callable] = None,
    disabled: bool = False
) -> bool:
    """
    Render action button.
    
    Returns:
        True if button was clicked
    """
```

**Example**:
```python
if render_action_button(
    label="Upload",
    icon="📤",
    type="primary",
    on_click=upload_files
):
    st.success("Upload initiated!")
```

---

#### 6.2 Confirm Modal
**File**: `components/actions/confirm_modal.py`

**Purpose**: Confirmation dialog for destructive actions

**Props**:
- `title` (str): Modal title
- `message` (str): Confirmation message
- `confirm_label` (str): Confirm button text
- `on_confirm` (Callable): Confirm callback

**API**:
```python
def show_confirm_modal(
    title: str,
    message: str,
    confirm_label: str = "Confirm",
    on_confirm: Optional[Callable] = None
) -> None:
    """Show confirmation modal"""
```

**Example**:
```python
if st.button("🗑️ Delete"):
    show_confirm_modal(
        title="Delete Files",
        message="Are you sure you want to delete 5 files?",
        confirm_label="Delete",
        on_confirm=lambda: delete_files(selected)
    )
```

---

## Component Usage Patterns

### Pattern 1: File Browser with Selection
```python
# Main file manager page
from components.navigation.tree_view import render_tree_view
from components.data_display.file_list import render_file_list
from components.feedback.empty_state import render_empty_state

# Layout
col1, col2 = st.columns([1, 3])

with col1:
    render_tree_view(
        bucket=current_bucket,
        on_select=lambda prefix: st.session_state.update({'prefix': prefix})
    )

with col2:
    files = cos_client.list_objects(current_bucket, current_prefix)
    
    if files:
        selected = render_file_list(files, selectable=True)
        if selected:
            st.write(f"Selected: {len(selected)} files")
    else:
        render_empty_state(
            icon="📭",
            title="No files found",
            description="This folder is empty"
        )
```

### Pattern 2: Dashboard with Metrics
```python
from components.data_display.metric_card import render_metric_card

st.title("🏠 Dashboard")

# Metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    render_metric_card("Total Files", "1,247", delta="+12", icon="📄")

with col2:
    render_metric_card("Total Size", "156 GB", delta="+2.3 GB", icon="💾")

with col3:
    render_metric_card("Buckets", "5", icon="🪣")

with col4:
    render_metric_card("Active Uploads", "3", icon="📤")
```

### Pattern 3: Upload Workflow
```python
from components.input.upload_zone import render_upload_zone
from components.feedback.progress_bar import render_progress_bar

st.title("📤 Upload Files")

# Upload zone
uploaded = render_upload_zone(
    bucket=current_bucket,
    prefix=current_prefix,
    on_upload=start_upload
)

# Progress tracking
if st.session_state.get('upload_in_progress'):
    render_progress_bar(
        total=st.session_state.upload_total,
        current=st.session_state.upload_current,
        label="Uploading files"
    )
```

---

## Styling Guidelines

### CSS Custom Properties
```css
/* Define in static/styles/components.css */

/* Buttons */
.btn-primary {
    background: var(--primary-brand);
    color: white;
    border-radius: 8px;
    padding: 12px 24px;
    font-weight: 600;
    transition: all 0.2s;
}

.btn-primary:hover {
    background: var(--primary-dark);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 110, 255, 0.3);
}

/* Cards */
.metric-card {
    background: white;
    border: 1px solid #e5e5e5;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* File rows */
.file-row {
    padding: 12px;
    border-bottom: 1px solid #e5e5e5;
    transition: background 0.2s;
}

.file-row:hover {
    background: #f9f9f9;
}
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_components/test_file_list.py
import pytest
from components.data_display.file_list import render_file_list

def test_file_list_renders():
    files = [
        {'key': 'test.csv', 'name': 'test.csv', 'size': 1024}
    ]
    # Test rendering
    pass

def test_file_list_selection():
    # Test selection functionality
    pass
```

### Integration Tests
```python
# tests/test_integration/test_file_manager.py
def test_file_manager_workflow():
    # Test complete workflow: browse → select → download
    pass
```

---

## Next Steps

1. **Implement core components** (Weeks 1-2)
   - Layout components (sidebar, header)
   - File list and tree view
   
2. **Build pages** (Weeks 3-5)
   - Home dashboard
   - File manager
   - Bucket management
   
3. **Add polish** (Week 6)
   - Animations and transitions
   - Error handling
   - Loading states
   
4. **Testing & documentation** (Weeks 7-8)
   - Unit tests
   - User documentation
   - Video tutorials

---

**Document Version**: 1.0  
**Last Updated**: December 18, 2025

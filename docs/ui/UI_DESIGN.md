# COS CLI - Data Management UI Design Document

## Executive Summary

This document outlines the design for a web-based UI for the Tencent COS CLI. The UI will provide a modern, intuitive interface for managing COS data while preserving the CLI's core functionality.

---

## 1. Design Assumptions

### Target Users
- Data scientists and researchers who prefer GUI over CLI
- Team members managing shared COS buckets
- Users performing bulk file operations
- Administrators monitoring storage usage

### Technical Stack
- **Framework**: Streamlit (matches reference repo pattern)
- **Backend**: COS CLI Python SDK (existing codebase)
- **Cloud**: Tencent Cloud COS
- **Authentication**: STS credentials, role assumption

### Design Constraints
- **Must adapt, not clone**: Borrow patterns but customize for COS operations
- **CLI parity**: UI should complement, not replace CLI
- **Performance**: Handle large file lists (1000+ objects)
- **Security**: Secure credential handling, presigned URLs

---

## 2. High-Level UI Layout

### Page Structure (Multi-Page Streamlit App)

```
cos-ui/
├── app.py                    # 🏠 Home / Dashboard
├── pages/
│   ├── file_manager.py       # 🗂️ Browse & Upload Files
│   ├── buckets.py            # 🪣 Bucket Management
│   ├── transfers.py          # 📤 Batch Upload/Download
│   └── settings.py           # ⚙️ Configuration & Credentials
├── src/
│   ├── config.py             # Configuration constants
│   ├── utils.py              # Shared utilities
│   └── cos_client.py         # COS client wrapper
├── components/
│   ├── file_browser.py       # Reusable file browser
│   ├── tree_view.py          # Folder tree component
│   └── upload_panel.py       # File upload component
└── static/
    ├── styles/
    │   └── page.css          # Custom CSS
    └── logos/
        └── tencent-logo.svg  # Tencent branding
```

---

## 3. Page-by-Page Layout

### 3.1 Home / Dashboard (app.py)

**Purpose**: Central hub for quick actions and system overview

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 COS Data Management UI                                   │
│ Modern interface for Tencent Cloud Object Storage           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ [System Health Metrics]                                     │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│ │ 🟢 COS   │ │ 📁 Active │ │ 📊 Total │ │ ⏱️ Session│       │
│ │Connected │ │  Bucket  │ │  Files   │ │   Time   │       │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                              │
│ [Quick Actions - 3 Columns]                                 │
│ ┌─────────────┬──────────────┬──────────────┐              │
│ │ 📁 Files    │ 🪣 Buckets   │ 📤 Transfers  │              │
│ │             │              │               │              │
│ │ • Browse    │ • List       │ • Batch Upload│              │
│ │ • Upload    │ • Create     │ • Sync Folders│              │
│ │ • Download  │ • Configure  │ • Progress    │              │
│ └─────────────┴──────────────┴──────────────┘              │
│                                                              │
│ [Recent Activity]                                           │
│ ┌─────────────────────────────────────────────┐            │
│ │ 🕐 Last Uploads | 📥 Last Downloads          │            │
│ │ • file1.csv     | • results.zip              │            │
│ │ • data.json     | • backup.tar.gz            │            │
│ └─────────────────────────────────────────────┘            │
│                                                              │
│ [Storage Statistics]                                        │
│ ┌─────────────────────────────────────────────┐            │
│ │ 📊 Bucket Usage by Type                     │            │
│ │ [Bar Chart: Documents | Data | Archives]    │            │
│ └─────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

**Components**:
- Metric cards (4-column grid)
- Quick action cards (3-column grid)
- Recent activity tabs
- Storage analytics chart

---

### 3.2 File Manager (pages/file_manager.py)

**Purpose**: Browse, search, and manage files in buckets (PRIMARY PAGE)

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ 🗂️ File Manager                                             │
│ Browse, upload, and download files from COS buckets         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ [Location Selector]                                         │
│ ┌────────────┬────────────────────────────────────────┐    │
│ │ 📍 Bucket: │ my-bucket ▼          [🔍 Browse]       │    │
│ │ 📂 Prefix: │ data/experiments/    [📤 Upload]       │    │
│ │            │                      [🔄 Refresh]      │    │
│ └────────────┴────────────────────────────────────────┘    │
│                                                              │
│ [Folder Tree View + File List View]                        │
│ ┌─────────────┬────────────────────────────────────────┐   │
│ │ 📁 Folders  │ 📄 Files                                │   │
│ │             │                                         │   │
│ │ ▼ data/     │ [Search: 🔍 Filter by name...]         │   │
│ │   ▼ exp001/ │ [Filters: 📊 Type ▼ | 📅 Date ▼]      │   │
│ │     • raw/  │                                         │   │
│ │     • proc/ │ ☑️ file1.csv  📊 2.4 MB  📅 2024-12-15│   │
│ │   • exp002/ │ ☐ data.json   💾 1.2 MB  📅 2024-12-14│   │
│ │             │ ☐ model.pkl   🧠 45 MB   📅 2024-12-13│   │
│ │ • archives/ │                                         │   │
│ │             │ [← Prev] Page 1/5 [Next →]            │   │
│ │             │ [📥 Download Selected] [🗑️ Delete]     │   │
│ └─────────────┴────────────────────────────────────────┘   │
│                                                              │
│ [File Details Panel - Expandable]                          │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ 📄 file1.csv                                        │    │
│ │ • Size: 2.4 MB                                      │    │
│ │ • Last Modified: 2024-12-15 10:30:00               │    │
│ │ • ETag: "abc123..."                                 │    │
│ │ • Storage Class: STANDARD                           │    │
│ │ [📥 Download] [🔗 Get Presigned URL] [🗑️ Delete]   │    │
│ └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Key Features**:
- Dual-pane layout (tree + list)
- Multi-select with checkboxes
- Real-time search and filtering
- Batch operations
- File preview for supported types
- Presigned URL generation

---

### 3.3 Buckets (pages/buckets.py)

**Purpose**: Create, configure, and manage buckets

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ 🪣 Bucket Management                                         │
│ Create and configure COS buckets                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ [Actions]                                                   │
│ [➕ Create New Bucket] [🔄 Refresh]                         │
│                                                              │
│ [Bucket List]                                               │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ 🪣 Name         │ 🌍 Region  │ 📊 Size │ 📅 Created │    │
│ ├─────────────────────────────────────────────────────┤    │
│ │ my-data-bucket │ ap-shanghai│ 2.3 GB │ 2024-01-15 │    │
│ │ backup-bucket  │ ap-beijing │ 45 GB  │ 2023-12-01 │    │
│ │ test-bucket    │ ap-shanghai│ 120 MB │ 2024-11-20 │    │
│ └─────────────────────────────────────────────────────┘    │
│                                                              │
│ [Bucket Details - Click to Expand]                         │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ 🪣 my-data-bucket                                   │    │
│ │ • Region: ap-shanghai                               │    │
│ │ • ACL: Private                                      │    │
│ │ • Versioning: Enabled                               │    │
│ │ • Lifecycle Rules: 2 active                         │    │
│ │                                                      │    │
│ │ [📂 Browse Files] [⚙️ Configure] [🗑️ Delete]        │    │
│ └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Key Features**:
- Bucket list with key metadata
- Quick navigation to file browser
- Bucket creation wizard
- Configuration management

---

### 3.4 Transfers (pages/transfers.py)

**Purpose**: Batch upload/download and sync operations

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ 📤 Batch Transfers                                          │
│ Upload, download, and sync multiple files                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ [Tabs: Upload | Download | Sync]                           │
│                                                              │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ 📤 BATCH UPLOAD                                     │    │
│ │                                                      │    │
│ │ [Source]                                            │    │
│ │ 📁 Local Directory: /home/user/data/                │    │
│ │ [📁 Select Directory...]                            │    │
│ │                                                      │    │
│ │ [Destination]                                       │    │
│ │ 🪣 Bucket: my-bucket ▼                              │    │
│ │ 📂 Prefix: uploads/batch_001/                       │    │
│ │                                                      │    │
│ │ [Options]                                           │    │
│ │ ☑️ Include subdirectories                           │    │
│ │ ☑️ Skip existing files                              │    │
│ │ ☐ Preserve file metadata                            │    │
│ │                                                      │    │
│ │ [Files to Upload: 47 files, 230 MB]                │    │
│ │                                                      │    │
│ │ [🚀 Start Upload]                                   │    │
│ │                                                      │    │
│ │ [Progress]                                          │    │
│ │ ████████████░░░░░░░░ 65% (30/47 files)             │    │
│ │ Current: uploading data_042.csv                     │    │
│ │ Speed: 12.5 MB/s | ETA: 2m 15s                     │    │
│ └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Key Features**:
- Folder selection
- Batch operations with progress tracking
- Parallel uploads/downloads
- Sync with conflict resolution
- Resume capability

---

### 3.5 Settings (pages/settings.py)

**Purpose**: Configure credentials and application preferences

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ Settings                                                  │
│ Configure credentials and application preferences            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ [Tabs: Credentials | Profiles | Preferences]               │
│                                                              │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ 🔐 CREDENTIALS                                      │    │
│ │                                                      │    │
│ │ Profile: default ▼                                  │    │
│ │                                                      │    │
│ │ Secret ID:     ****************                     │    │
│ │ Secret Key:    ****************                     │    │
│ │ Region:        ap-shanghai ▼                        │    │
│ │ Default Bucket: my-bucket                           │    │
│ │                                                      │    │
│ │ [Test Connection] [Save]                            │    │
│ │                                                      │    │
│ │ Status: 🟢 Connected (Last checked: 2 mins ago)    │    │
│ │                                                      │    │
│ │ [Advanced: STS Tokens & Role Assumption]           │    │
│ └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Component Breakdown (Reusable Components)

### 4.1 Core Components

| Component | File | Purpose | Props |
|-----------|------|---------|-------|
| `FileTreeView` | `components/tree_view.py` | Hierarchical folder navigation | `bucket`, `prefix`, `on_select` |
| `FileListView` | `components/file_browser.py` | Table with file details | `files`, `selectable`, `on_action` |
| `UploadPanel` | `components/upload_panel.py` | File upload interface | `bucket`, `prefix`, `on_complete` |
| `MetricCard` | `components/metrics.py` | Dashboard metric display | `label`, `value`, `delta`, `icon` |
| `ProgressTracker` | `components/progress.py` | Upload/download progress | `total`, `current`, `speed` |
| `BucketSelector` | `components/selectors.py` | Bucket dropdown | `on_select`, `default` |
| `FilePreview` | `components/preview.py` | Preview files (CSV, JSON, images) | `file_key`, `bucket` |
| `ActionButton` | `components/buttons.py` | Styled action buttons | `label`, `icon`, `on_click`, `type` |

### 4.2 Layout Components

| Component | Purpose |
|-----------|---------|
| `Sidebar` | Navigation menu with logo |
| `PageHeader` | Page title + breadcrumbs |
| `StatusBar` | Connection status indicator |
| `EmptyState` | No-data placeholder |
| `LoadingSpinner` | Async operation indicator |

### 4.3 Utility Components

| Component | Purpose |
|-----------|---------|
| `SearchBar` | Real-time file search |
| `FilterPanel` | Multi-criteria filtering |
| `Pagination` | List pagination controls |
| `ConfirmDialog` | Destructive action confirmation |

---

## 5. Design Tokens (Visual Style Guide)

### 5.1 Color Palette

```css
/* Primary Colors */
--primary-brand:     #006EFF;  /* Tencent Blue */
--primary-dark:      #0052CC;
--primary-light:     #4D9FFF;

/* Secondary Colors */
--secondary:         #00C9A7;  /* Success Green */
--warning:           #FFB84D;
--danger:            #FF4D4F;
--info:              #4DA6FF;

/* Neutrals */
--neutral-900:       #1A1A1A;  /* Text */
--neutral-700:       #4A4A4A;
--neutral-500:       #8C8C8C;
--neutral-300:       #D9D9D9;
--neutral-100:       #F5F5F5;  /* Background */
--white:             #FFFFFF;

/* Semantic Colors */
--success:           #52C41A;
--error:             #FF4D4F;
--folder:            #FFD666;
--file:              #8C8C8C;
```

### 5.2 Typography

```css
/* Font Family */
--font-primary:      'Inter', 'Helvetica Neue', sans-serif;
--font-mono:         'JetBrains Mono', 'Courier New', monospace;

/* Font Sizes */
--text-xs:           0.75rem;   /* 12px - captions */
--text-sm:           0.875rem;  /* 14px - body small */
--text-base:         1rem;      /* 16px - body */
--text-lg:           1.125rem;  /* 18px - subheading */
--text-xl:           1.25rem;   /* 20px - heading 3 */
--text-2xl:          1.5rem;    /* 24px - heading 2 */
--text-3xl:          2rem;      /* 32px - heading 1 */

/* Font Weights */
--font-normal:       400;
--font-medium:       500;
--font-semibold:     600;
--font-bold:         700;
```

### 5.3 Spacing Scale

```css
--spacing-xs:        0.25rem;  /* 4px */
--spacing-sm:        0.5rem;   /* 8px */
--spacing-md:        1rem;     /* 16px */
--spacing-lg:        1.5rem;   /* 24px */
--spacing-xl:        2rem;     /* 32px */
--spacing-2xl:       3rem;     /* 48px */
```

### 5.4 Component Styles

#### Buttons
```css
.btn-primary {
  background: var(--primary-brand);
  color: var(--white);
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: var(--font-semibold);
  transition: all 0.2s;
}

.btn-primary:hover {
  background: var(--primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 110, 255, 0.3);
}
```

#### Cards
```css
.card {
  background: var(--white);
  border: 1px solid var(--neutral-300);
  border-radius: 12px;
  padding: var(--spacing-lg);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
```

#### Tables
```css
.table-row {
  border-bottom: 1px solid var(--neutral-300);
  padding: var(--spacing-md);
  transition: background 0.2s;
}

.table-row:hover {
  background: var(--neutral-100);
}
```

---

## 6. Interaction Patterns

### 6.1 Navigation
- **Sidebar**: Persistent navigation to all pages
- **Breadcrumbs**: Show current location in bucket hierarchy
- **Back Button**: Return to previous folder/page

### 6.2 File Selection
- **Single Select**: Click row
- **Multi Select**: Checkboxes
- **Select All**: Checkbox in header
- **Shift+Click**: Range selection

### 6.3 File Operations
- **Upload**: Drag-and-drop or file picker
- **Download**: Click download icon or batch download button
- **Delete**: Confirmation modal before deletion
- **Preview**: Click eye icon (CSV, JSON, images)

### 6.4 Loading States
- **Skeleton Screens**: While loading file lists
- **Progress Bars**: For upload/download operations
- **Spinners**: For quick operations (< 2s)
- **Toast Notifications**: Success/error feedback

### 6.5 Error Handling
- **Inline Errors**: Below form fields
- **Toast Notifications**: For operation failures
- **Retry Buttons**: For failed uploads/downloads
- **Error Details**: Expandable error messages

---

## 7. Accessibility Features

### 7.1 Keyboard Navigation
- `Tab`: Navigate between elements
- `Enter`: Activate buttons/links
- `Space`: Toggle checkboxes
- `Escape`: Close modals/dropdowns
- `Arrow Keys`: Navigate lists

### 7.2 Screen Reader Support
- Semantic HTML (`<nav>`, `<main>`, `<article>`)
- ARIA labels for icons
- ARIA live regions for dynamic content
- Focus management for modals

### 7.3 Visual Accessibility
- Minimum contrast ratio: 4.5:1
- Focus indicators (2px outline)
- No color-only information
- Scalable text (rem units)

---

## 8. Responsive Design Breakpoints

```css
/* Mobile First */
--breakpoint-sm:   640px;   /* Small tablets */
--breakpoint-md:   768px;   /* Tablets */
--breakpoint-lg:   1024px;  /* Desktop */
--breakpoint-xl:   1280px;  /* Large desktop */
```

### Layout Adaptations
- **Mobile (< 640px)**: Stacked layout, collapsed sidebar
- **Tablet (640-1024px)**: Hybrid layout, expandable sidebar
- **Desktop (> 1024px)**: Full dual-pane layout

---

## 9. ASCII Wireframe: File Manager Page

```
┌────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                  │
│ ┌──────────────────────────────────────────────────────────────────┐  │
│ │ [LOGO] COS File Manager         [🔔] [👤] admin [⚙️] Settings   │  │
│ └──────────────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────────────┤
│ SIDEBAR         │ MAIN CONTENT                                         │
│ ┌─────────────┐ │ ┌──────────────────────────────────────────────┐   │
│ │ 🏠 Dashboard│ │ │ 🗂️ File Manager                              │   │
│ │ 🗂️ Files *  │ │ │ Browse and manage files in COS buckets       │   │
│ │ 🪣 Buckets  │ │ └──────────────────────────────────────────────┘   │
│ │ 📤 Transfers│ │                                                      │
│ │ ⚙️ Settings │ │ ┌──────────────────────────────────────────────┐   │
│ │             │ │ │ 📍 my-bucket / data / experiments /          │   │
│ │             │ │ │ [🔍 Browse] [📤 Upload] [🔄 Refresh]         │   │
│ │             │ │ └──────────────────────────────────────────────┘   │
│ │             │ │                                                      │
│ │             │ │ ┌──────────┬─────────────────────────────────────┐ │
│ │             │ │ │ FOLDERS  │ FILES                                │ │
│ │             │ │ │          │                                      │ │
│ │             │ │ │ ▼ data/  │ [🔍 Search...] [📊 Type] [📅 Date] │ │
│ │             │ │ │  ▼ exp1/ │ ┌────────────────────────────────┐ │ │
│ │             │ │ │   • raw  │ │ ☑️ file1.csv    2.4 MB  Dec 15│ │ │
│ │             │ │ │   • proc │ │ ☐ data.json     1.2 MB  Dec 14│ │ │
│ │             │ │ │  • exp2  │ │ ☐ model.pkl     45 MB   Dec 13│ │ │
│ │             │ │ │          │ │                                │ │ │
│ │             │ │ │          │ │ [Prev] Page 1/5 [Next]         │ │ │
│ │             │ │ │          │ └────────────────────────────────┘ │ │
│ │             │ │ │          │ [📥 Download] [🗑️ Delete]          │ │
│ └─────────────┘ │ └──────────┴─────────────────────────────────────┘ │
│                 │                                                      │
│                 │ ┌──────────────────────────────────────────────┐   │
│                 │ │ 📄 FILE DETAILS: file1.csv                   │   │
│                 │ │ Size: 2.4 MB | Modified: Dec 15, 2024       │   │
│                 │ │ [📥 Download] [🔗 Presigned URL] [🗑️ Delete]│   │
│                 │ └──────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Implementation Plan

### Phase 1: Foundation (Week 1-2)
- Set up Streamlit multi-page app structure
- Create `src/cos_client.py` wrapper around existing CLI
- Implement authentication and session management
- Design and implement base layout components

### Phase 2: File Manager (Week 3-4)
- Build file list view with pagination
- Implement folder tree navigation
- Add file upload panel
- Add download functionality
- Implement search and filtering

### Phase 3: Bucket Management (Week 5)
- Bucket list view
- Bucket creation wizard
- Bucket configuration UI

### Phase 4: Batch Operations (Week 6-7)
- Batch upload UI
- Batch download UI
- Sync functionality
- Progress tracking

### Phase 5: Polish & Testing (Week 8)
- Settings page
- Error handling improvements
- Performance optimization
- User testing and feedback

---

## 11. Technical Implementation Notes

### COS Client Wrapper
```python
# src/cos_client.py
from cos.client import COSClient as BaseCOSClient
from cos.auth import COSAuthenticator
from cos.config import ConfigManager

class WebCOSClient:
    """Web UI wrapper around COS CLI client"""
    
    def __init__(self, profile="default"):
        config = ConfigManager(profile)
        auth = COSAuthenticator(config)
        self.client = auth.authenticate()
    
    def list_files(self, bucket, prefix="", limit=1000):
        """List files with pagination support"""
        # Use existing CLI list_objects method
        pass
    
    def upload_file(self, file_obj, bucket, key, progress_callback=None):
        """Upload file with progress tracking"""
        # Use existing CLI upload method with progress callback
        pass
```

### State Management
```python
# Use Streamlit session state for:
- st.session_state.current_bucket
- st.session_state.current_prefix
- st.session_state.selected_files
- st.session_state.upload_progress
- st.session_state.credentials
```

### Caching Strategy
```python
@st.cache_data(ttl=300)  # 5-minute cache
def list_buckets():
    """Cache bucket list"""
    pass

@st.cache_data(ttl=60)  # 1-minute cache
def list_objects(bucket, prefix):
    """Cache file lists"""
    pass
```

---

## 12. Security Considerations

1. **Credential Storage**: Store in session state, never in localStorage
2. **Presigned URLs**: Short expiration (1 hour max)
3. **HTTPS Only**: Force HTTPS in production
4. **Input Validation**: Sanitize all user inputs
5. **Rate Limiting**: Implement on API endpoints
6. **CORS**: Configure properly for S3 operations
7. **Authentication**: Support role-based access if needed

---

## 13. Performance Optimizations

1. **Lazy Loading**: Load files on-demand (pagination)
2. **Virtual Scrolling**: For large file lists (1000+ files)
3. **Debounced Search**: Delay search while typing
4. **Parallel Uploads**: Use multiprocessing for batch uploads
5. **Compressed Transfers**: Enable compression where possible
6. **Caching**: Cache bucket lists and metadata

---

## 14. Comparison with Reference

### Borrowed Patterns ✅
- Multi-page Streamlit structure
- File manager with tree + list view
- Upload panel with progress tracking
- Metric cards on dashboard
- Color scheme (adapted for Tencent branding)
- Component organization
- Session state management

### Adapted/Different ❌
- **Storage Backend**: COS instead of S3
- **Primary Focus**: File management (not DAG orchestration)
- **Branding**: Tencent blue
- **Bucket Management**: Full bucket CRUD (not just file browsing)
- **Batch Operations**: More emphasis on sync/transfer

---

## 15. Next Steps

1. **Approval**: Review this design document with stakeholders
2. **Prototype**: Build clickable prototype in Figma (optional)
3. **Implementation**: Follow 8-week implementation plan
4. **Testing**: User acceptance testing with 5-10 users
5. **Documentation**: User guide and video tutorials
6. **Deployment**: Deploy to internal cloud environment

---

## Appendix A: File Extension Icons

```python
FILE_EXTENSION_EMOJIS = {
    'CSV': '📊',
    'JSON': '⚙️',
    'TXT': '📝',
    'LOG': '📋',
    'PY': '🐍',
    'SH': '📜',
    'ZIP': '📦',
    'TAR': '📦',
    'GZ': '📦',
    'PARQUET': '📈',
    'XLSX': '📊',
    'PDF': '📄',
    'PNG': '🖼️',
    'JPG': '🖼️',
    'MP4': '🎬',
    'MP3': '🎵',
}
```

---

## Appendix B: Sample Code Snippets

### File Upload Component
```python
def render_upload_panel(bucket, prefix):
    uploaded_files = st.file_uploader(
        "Select files to upload",
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for file in uploaded_files:
            progress = st.progress(0)
            cos_client.upload_file(
                file, bucket, f"{prefix}{file.name}",
                progress_callback=progress.update
            )
```

### File List with Selection
```python
def render_file_list(files):
    selected = []
    for file in files:
        col1, col2, col3, col4 = st.columns([1, 5, 2, 2])
        with col1:
            if st.checkbox("", key=file['key']):
                selected.append(file)
        with col2:
            st.write(f"{get_file_emoji(file)} {file['name']}")
        with col3:
            st.write(format_size(file['size']))
        with col4:
            st.write(format_date(file['modified']))
    return selected
```

---

**Document Version**: 1.0  
**Last Updated**: December 18, 2025  
**Author**: Senior UI/UX Designer & Frontend Engineer  
**Status**: Ready for Review

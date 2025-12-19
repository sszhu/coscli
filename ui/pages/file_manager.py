"""File Manager Page - Browse, upload, and manage files in COS buckets.

Refactored Phase 2 Implementation: Clean separation of concerns with extracted
helper functions and reusable components.
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.src.page_utils import setup_page_simple
from ui.src.file_operations import (
    filter_files,
    sort_files,
    paginate_files,
    delete_files_batch,
    upload_files_batch,
    download_file,
    get_presigned_url,
    create_folder,
    load_files_and_folders,
)
from ui.components.widgets import (
    render_confirmation_dialog,
    render_modal_dialog,
    render_search_filter_bar,
    render_pagination_controls,
    render_file_table,
    render_bulk_actions,
)
from ui.src.config import DEFAULT_BUCKET, DEFAULT_PREFIX, DEFAULT_PAGE_SIZE, FOLDER_EMOJI
from ui.src.utils import get_cos_client, init_session_state, render_bucket_prefix_selector
from ui.components.status_indicators import render_empty_state

# ============================================================================
# PAGE SETUP
# ============================================================================

setup_page_simple(
    title="File Manager",
    icon="🗂️",
    page_id="files",
    caption="Browse, upload, and manage files in COS buckets"
)

# ============================================================================
# SESSION STATE
# ============================================================================

init_session_state({
    'current_bucket': DEFAULT_BUCKET,
    'current_prefix': DEFAULT_PREFIX,
    'selected_files': [],
    'file_list': [],
    'folder_list': [],
    'page_number': 1,
    'page_size': DEFAULT_PAGE_SIZE,
    'sort_by': 'name',
    'sort_order': 'asc',
    'filter_type': 'all',
    'search_query': '',
    'show_upload_panel': False,
    'show_delete_confirm': False,
    'show_new_folder': False,
})

# ============================================================================
# LOCATION SELECTOR
# ============================================================================

st.markdown("### 📍 Location")

def handle_location_change():
    """Reset file list when bucket/prefix changes."""
    st.session_state.file_list = []
    st.session_state.selected_files = []
    st.rerun()

bucket, prefix = render_bucket_prefix_selector(on_change_callback=handle_location_change)

if not bucket:
    st.stop()

st.divider()

# ============================================================================
# ACTION BAR
# ============================================================================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🔄 Refresh", use_container_width=True):
        st.session_state.file_list = []
        st.rerun()

with col2:
    if st.button("📤 Upload", use_container_width=True, type="primary"):
        st.session_state.show_upload_panel = not st.session_state.show_upload_panel
        st.rerun()

with col3:
    num_selected = len(st.session_state.selected_files)
    if st.button(
        f"🗑️ Delete ({num_selected})",
        use_container_width=True,
        disabled=(num_selected == 0)
    ):
        st.session_state.show_delete_confirm = True

with col4:
    if st.button("➕ Folder", use_container_width=True):
        st.session_state.show_new_folder = True

with col5:
    has_prefix = bool(st.session_state.current_prefix)
    if st.button("⬆️ Up", use_container_width=True, disabled=not has_prefix):
        parts = st.session_state.current_prefix.rstrip('/').split('/')
        if len(parts) > 1:
            st.session_state.current_prefix = '/'.join(parts[:-1]) + '/'
        else:
            st.session_state.current_prefix = ''
        st.session_state.file_list = []
        st.rerun()

st.markdown("")

# ============================================================================
# UPLOAD PANEL
# ============================================================================

if st.session_state.show_upload_panel:
    render_modal_dialog(
        title="📤 Upload Files",
        input_config={
            'type': 'file',
            'label': "Choose files",
            'kwargs': {'accept_multiple_files': True},
        },
        on_submit=lambda files: (
            upload_files_batch(
                st.session_state.current_bucket,
                st.session_state.current_prefix,
                files
            ),
            setattr(st.session_state, 'show_upload_panel', False),
            setattr(st.session_state, 'file_list', []),
            st.rerun()
        ),
        on_cancel=lambda: (
            setattr(st.session_state, 'show_upload_panel', False),
            st.rerun()
        ),
        submit_label="🚀 Upload",
    )

# ============================================================================
# NEW FOLDER DIALOG
# ============================================================================

if st.session_state.show_new_folder:
    def create_folder_callback(folder_name):
        try:
            folder_path = st.session_state.current_prefix + folder_name
            create_folder(st.session_state.current_bucket, folder_path)
            st.success(f"✅ Created: {folder_name}")
            st.session_state.show_new_folder = False
            st.session_state.file_list = []
            st.rerun()
        except Exception as e:
            st.error(f"Failed: {str(e)}")
    
    render_modal_dialog(
        title="➕ Create Folder",
        input_config={
            'type': 'text',
            'label': "Folder name",
            'kwargs': {'placeholder': 'my-folder'},
        },
        on_submit=create_folder_callback,
        on_cancel=lambda: (
            setattr(st.session_state, 'show_new_folder', False),
            st.rerun()
        ),
        submit_label="✅ Create",
    )

# ============================================================================
# DELETE CONFIRMATION
# ============================================================================

if st.session_state.show_delete_confirm:
    render_confirmation_dialog(
        message=f"⚠️ Delete {len(st.session_state.selected_files)} file(s)?",
        on_confirm=lambda: (
            delete_files_batch(
                st.session_state.current_bucket,
                st.session_state.selected_files
            ),
            setattr(st.session_state, 'show_delete_confirm', False),
            setattr(st.session_state, 'selected_files', []),
            setattr(st.session_state, 'file_list', []),
            st.rerun()
        ),
        on_cancel=lambda: (
            setattr(st.session_state, 'show_delete_confirm', False),
            st.rerun()
        ),
    )

# ============================================================================
# SEARCH & FILTER BAR
# ============================================================================

st.markdown("### 🔍 Search & Filter")

sort_options = {
    'Name ↑': ('name', 'asc'),
    'Name ↓': ('name', 'desc'),
    'Size ↑': ('size', 'asc'),
    'Size ↓': ('size', 'desc'),
    'Date ↑': ('date', 'asc'),
    'Date ↓': ('date', 'desc'),
}

# Find current sort display
current_sort_display = 'Name ↑'
for display, (by, order) in sort_options.items():
    if by == st.session_state.sort_by and order == st.session_state.sort_order:
        current_sort_display = display
        break

render_search_filter_bar(
    search_value=st.session_state.search_query,
    filter_options=['all', '.csv', '.json', '.txt', '.py', '.zip'],
    filter_value=st.session_state.filter_type,
    sort_options=sort_options,
    sort_value=current_sort_display,
    on_search_change=lambda q: (
        setattr(st.session_state, 'search_query', q),
        setattr(st.session_state, 'page_number', 1),
    ),
    on_filter_change=lambda f: (
        setattr(st.session_state, 'filter_type', f),
        setattr(st.session_state, 'page_number', 1),
    ),
    on_sort_change=lambda s: (
        setattr(st.session_state, 'sort_by', sort_options[s][0]),
        setattr(st.session_state, 'sort_order', sort_options[s][1]),
    ),
)

st.divider()

# ============================================================================
# LOAD FILES
# ============================================================================

if not st.session_state.file_list:
    with st.spinner("Loading..."):
        files, folders = load_files_and_folders(
            st.session_state.current_bucket,
            st.session_state.current_prefix
        )
        st.session_state.file_list = files
        st.session_state.folder_list = folders

# ============================================================================
# FOLDERS
# ============================================================================

if st.session_state.folder_list:
    st.markdown("### 📁 Folders")
    
    for folder in st.session_state.folder_list:
        folder_name = folder.rstrip('/').split('/')[-1]
        if st.button(
            f"{FOLDER_EMOJI} {folder_name}/",
            key=f"fld_{folder}",
            use_container_width=True
        ):
            st.session_state.current_prefix = folder
            st.session_state.file_list = []
            st.rerun()
    
    st.divider()

# ============================================================================
# FILES
# ============================================================================

st.markdown("### 📄 Files")

# Apply filters, sorting, and pagination
filtered = filter_files(
    st.session_state.file_list,
    st.session_state.search_query,
    st.session_state.filter_type
)
sorted_files = sort_files(
    filtered,
    st.session_state.sort_by,
    st.session_state.sort_order
)
page_files, page_num, total_pages = paginate_files(
    sorted_files,
    st.session_state.page_number,
    st.session_state.page_size
)

st.caption(
    f"Showing {len(page_files)} of {len(sorted_files)} "
    f"(Total: {len(st.session_state.file_list)})"
)

if not page_files:
    render_empty_state(
        title="No Files Found",
        message="Adjust your filters or upload files.",
        icon="📭"
    )
else:
    # File download handler
    def handle_download(file):
        try:
            content = download_file(st.session_state.current_bucket, file)
            st.download_button(
                label=f"💾 Save {file['name']}",
                data=content,
                file_name=file['name'],
                mime='application/octet-stream',
                key=f"save_{file['key']}"
            )
        except Exception as e:
            st.error(f"Failed: {str(e)}")
    
    # URL generation handler
    def handle_url(file):
        try:
            url = get_presigned_url(
                st.session_state.current_bucket,
                file['key'],
                expires_in=3600
            )
            st.code(url, language=None)
            st.caption("⏱️ Expires in 1 hour")
        except Exception as e:
            st.error(f"Failed: {str(e)}")
    
    # Render file table
    render_file_table(
        files=page_files,
        selected_keys=st.session_state.selected_files,
        on_selection_change=lambda keys: setattr(
            st.session_state,
            'selected_files',
            keys
        ),
        on_download=handle_download,
        on_url=handle_url,
    )

# ============================================================================
# PAGINATION
# ============================================================================

render_pagination_controls(
    page_num=page_num,
    total_pages=total_pages,
    on_page_change=lambda p: (
        setattr(st.session_state, 'page_number', p),
        st.rerun()
    ),
)

# ============================================================================
# BULK ACTIONS
# ============================================================================

render_bulk_actions(
    selected_count=len(st.session_state.selected_files),
    on_clear=lambda: (
        setattr(st.session_state, 'selected_files', []),
        st.rerun()
    ),
)

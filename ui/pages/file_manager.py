"""File Manager Page - Browse and manage files in COS buckets."""

import streamlit as st
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.src.config import DEFAULT_BUCKET, FILE_EXTENSION_EMOJIS, FOLDER_EMOJI
from ui.src.utils import (
    inject_global_styles,
    render_sidebar_navigation,
    get_cos_client,
    format_size,
    format_datetime,
    get_file_emoji,
    handle_error,
    init_session_state,
)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="File Manager - COS Data Manager",
    page_icon="🗂️",
    layout="wide"
)

inject_global_styles()

# ============================================================================
# INITIALIZE SESSION STATE
# ============================================================================

init_session_state({
    'current_bucket': DEFAULT_BUCKET,
    'current_prefix': '',
    'selected_files': [],
    'show_upload_panel': False,
    'file_list': [],
})

# ============================================================================
# SIDEBAR
# ============================================================================

render_sidebar_navigation(current_page="files")

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.title("🗂️ File Manager")
st.caption("Browse, upload, and download files from COS buckets")
st.markdown("")

# ============================================================================
# LOCATION SELECTOR
# ============================================================================

st.markdown("### 📍 Current Location")

col1, col2 = st.columns([1, 2])

with col1:
    # Get COS client
    cos_client = get_cos_client()
    
    if cos_client:
        try:
            # List available buckets
            from cos.client import COSClient
            client_wrapper = COSClient(cos_client)
            buckets = client_wrapper.list_buckets()
            bucket_names = [b['Name'] for b in buckets]
            
            current_bucket = st.selectbox(
                "🪣 Bucket",
                options=bucket_names,
                index=bucket_names.index(st.session_state.current_bucket) 
                      if st.session_state.current_bucket in bucket_names else 0,
                key="bucket_selector"
            )
            st.session_state.current_bucket = current_bucket
        except Exception as e:
            st.error(f"Failed to load buckets: {str(e)}")
            current_bucket = st.session_state.current_bucket
    else:
        st.warning("COS client not initialized. Please configure credentials in Settings.")
        current_bucket = st.text_input("🪣 Bucket", value=st.session_state.current_bucket)

with col2:
    current_prefix = st.text_input(
        "📂 Prefix (path)",
        value=st.session_state.current_prefix,
        placeholder="data/experiments/",
        help="Enter folder path (prefix) within the bucket",
        key="prefix_input"
    )
    st.session_state.current_prefix = current_prefix

# Display current path
if current_bucket:
    st.info(f"📍 Current location: `cos://{current_bucket}/{current_prefix}`")

st.divider()

# ============================================================================
# ACTION BUTTONS
# ============================================================================

col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

with col1:
    if st.button("🔍 Browse Files", type="primary", use_container_width=True):
        if cos_client and current_bucket:
            try:
                with st.spinner("Loading files..."):
                    # List objects
                    from cos.client import COSClient
                    client_wrapper = COSClient(cos_client, current_bucket)
                    response = client_wrapper.list_objects(prefix=current_prefix)
                    
                    # Parse files
                    files = []
                    for obj in response.get('Contents', []):
                        if not obj['Key'].endswith('/'):  # Skip directories
                            files.append({
                                'key': obj['Key'],
                                'name': Path(obj['Key']).name,
                                'size': obj['Size'],
                                'last_modified': obj['LastModified'],
                            })
                    
                    st.session_state.file_list = files
                    
                    if files:
                        st.success(f"✅ Found {len(files)} file(s)")
                    else:
                        st.info("📭 No files found in this location")
                        
            except Exception as e:
                handle_error(e, "Failed to list files")
        else:
            st.warning("Please configure COS client and select a bucket")

with col2:
    if st.button("📤 Upload Files", use_container_width=True):
        st.session_state.show_upload_panel = not st.session_state.show_upload_panel

with col3:
    if st.button("🔄 Refresh", use_container_width=True):
        if st.session_state.file_list:
            # Trigger reload
            st.rerun()

with col4:
    st.button("⚙️", help="More options", use_container_width=True)

# ============================================================================
# UPLOAD PANEL
# ============================================================================

if st.session_state.show_upload_panel:
    with st.expander("📤 Upload Files", expanded=True):
        st.caption(f"Uploading to: `cos://{current_bucket}/{current_prefix}`")
        
        uploaded_files = st.file_uploader(
            "Select files to upload",
            accept_multiple_files=True,
            key="file_uploader"
        )
        
        if uploaded_files:
            st.write(f"**{len(uploaded_files)} file(s) selected:**")
            
            # Show file preview
            for file in uploaded_files:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"{get_file_emoji(file.name)} {file.name}")
                with col_b:
                    st.caption(format_size(len(file.getvalue())))
            
            # Upload button
            if st.button("🚀 Upload Now", type="primary"):
                if cos_client:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    success_count = 0
                    for idx, file in enumerate(uploaded_files):
                        try:
                            status_text.text(f"Uploading {file.name}...")
                            
                            # Upload file
                            from cos.client import COSClient
                            client_wrapper = COSClient(cos_client, current_bucket)
                            key = f"{current_prefix}{file.name}"
                            
                            client_wrapper.put_object(
                                key=key,
                                body=file.getvalue()
                            )
                            
                            success_count += 1
                        except Exception as e:
                            st.error(f"Failed to upload {file.name}: {str(e)}")
                        
                        progress_bar.progress((idx + 1) / len(uploaded_files))
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    if success_count == len(uploaded_files):
                        st.success(f"✅ Uploaded {success_count} file(s) successfully!")
                    else:
                        st.warning(f"⚠️ Uploaded {success_count}/{len(uploaded_files)} files")
                    
                    # Hide upload panel and refresh
                    st.session_state.show_upload_panel = False
                    st.rerun()
                else:
                    st.error("COS client not initialized")

st.markdown("")

# ============================================================================
# FILE LIST
# ============================================================================

if st.session_state.file_list:
    st.markdown(f"### 📄 Files ({len(st.session_state.file_list)})")
    st.caption("Select files to download or delete")
    st.markdown("")
    
    # Search and filter
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Search",
            placeholder="Filter by filename...",
            label_visibility="collapsed"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            options=["Name", "Size", "Date"],
            label_visibility="collapsed"
        )
    
    with col3:
        sort_order = st.selectbox(
            "Order",
            options=["↑ Asc", "↓ Desc"],
            label_visibility="collapsed"
        )
    
    # Filter files
    filtered_files = st.session_state.file_list
    if search_query:
        filtered_files = [f for f in filtered_files if search_query.lower() in f['name'].lower()]
    
    # Sort files
    reverse = "Desc" in sort_order
    if sort_by == "Name":
        filtered_files = sorted(filtered_files, key=lambda x: x['name'], reverse=reverse)
    elif sort_by == "Size":
        filtered_files = sorted(filtered_files, key=lambda x: x['size'], reverse=reverse)
    elif sort_by == "Date":
        filtered_files = sorted(filtered_files, key=lambda x: x['last_modified'], reverse=reverse)
    
    st.markdown("")
    
    # File table
    if filtered_files:
        # Header
        col1, col2, col3, col4, col5 = st.columns([1, 4, 2, 2, 2])
        with col1:
            st.markdown("**☑️**")
        with col2:
            st.markdown("**📄 Name**")
        with col3:
            st.markdown("**📦 Size**")
        with col4:
            st.markdown("**📅 Modified**")
        with col5:
            st.markdown("**Actions**")
        
        st.divider()
        
        # File rows
        selected_files = []
        for file in filtered_files:
            col1, col2, col3, col4, col5 = st.columns([1, 4, 2, 2, 2])
            
            with col1:
                if st.checkbox("", key=f"select_{file['key']}", label_visibility="collapsed"):
                    selected_files.append(file)
            
            with col2:
                st.write(f"{get_file_emoji(file['name'])} {file['name']}")
            
            with col3:
                st.caption(format_size(file['size']))
            
            with col4:
                st.caption(format_datetime(file['last_modified']))
            
            with col5:
                if st.button("⬇️", key=f"download_{file['key']}", help="Download"):
                    st.info("Download functionality coming soon!")
        
        # Batch actions
        if selected_files:
            st.divider()
            st.markdown(f"**{len(selected_files)} file(s) selected**")
            
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("📥 Download Selected", use_container_width=True):
                    st.info("Batch download coming soon!")
            with col2:
                if st.button("🗑️ Delete Selected", type="primary", use_container_width=True):
                    st.warning("Delete functionality coming soon!")
    else:
        st.info("📭 No files match your search criteria")

elif not cos_client:
    st.info("👈 Please configure COS credentials in Settings to get started")
else:
    st.info("👆 Click 'Browse Files' to load files from the selected location")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("")
st.divider()

st.caption("""
💡 **Tips:**
- Use drag & drop to upload multiple files
- Search to quickly find files
- Select multiple files for batch operations

🚧 **Work in Progress:**
- Download functionality
- Delete operations
- File preview
- Folder navigation tree
""")

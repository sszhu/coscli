"""
COS Data Manager - Main Application Entry Point

A modern web UI for Tencent Cloud Object Storage (COS) management.
Built with Streamlit, inspired by AutoLEAD UI design patterns.
"""

import streamlit as st
from datetime import datetime
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.src.config import (
    LOGO_PATH,
    APP_TITLE,
    APP_SUBTITLE,
    DEFAULT_BUCKET,
    DEFAULT_PREFIX,
)
from ui.src.utils import (
    inject_global_styles,
    render_sidebar_navigation,
    get_cos_client,
)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="COS Data Manager",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS
inject_global_styles()

# ============================================================================
# INITIALIZE SESSION STATE
# ============================================================================

if "session_start_time" not in st.session_state:
    st.session_state["session_start_time"] = datetime.now()

if "current_bucket" not in st.session_state:
    st.session_state["current_bucket"] = DEFAULT_BUCKET

if "current_prefix" not in st.session_state:
    st.session_state["current_prefix"] = DEFAULT_PREFIX

if "recent_uploads" not in st.session_state:
    st.session_state["recent_uploads"] = []

if "recent_downloads" not in st.session_state:
    st.session_state["recent_downloads"] = []

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

render_sidebar_navigation(current_page="home")

# ============================================================================
# MAIN PAGE CONTENT
# ============================================================================

st.title("🚀 COS Data Manager")
st.markdown("##### Modern interface for Tencent Cloud Object Storage")
st.markdown("")

# ============================================================================
# SYSTEM HEALTH DASHBOARD
# ============================================================================

st.markdown("### 📊 System Overview")
st.caption("Quick insights into your COS environment")
st.markdown("")

col1, col2, col3, col4 = st.columns(4)

with col1:
    # COS Connection Status
    cos_client = get_cos_client()
    connection_status = "Connected" if cos_client else "Disconnected"
    connection_icon = "🟢" if cos_client else "🔴"
    
    st.metric(
        label=f"{connection_icon} COS Status",
        value=connection_status,
        delta="Healthy" if cos_client else "Check Credentials"
    )

with col2:
    # Active bucket
    current_bucket = st.session_state.get("current_bucket", "None")
    st.metric(
        label="📁 Active Bucket",
        value=current_bucket if current_bucket else "None",
        delta="Click to change"
    )

with col3:
    # Recent uploads
    upload_count = len(st.session_state.get("recent_uploads", []))
    st.metric(
        label="📤 Recent Uploads",
        value=upload_count,
        delta="This session"
    )

with col4:
    # Session time
    if "session_start_time" in st.session_state:
        session_duration = datetime.now() - st.session_state["session_start_time"]
        minutes = int(session_duration.total_seconds() / 60)
        st.metric(
            label="⏱️ Session Time",
            value=f"{minutes} min",
            delta="Active"
        )

st.markdown("")
st.divider()

# ============================================================================
# QUICK ACTIONS PANEL
# ============================================================================

st.markdown("### ⚡ Quick Actions")
st.caption("Navigate to common tasks with one click")
st.markdown("")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("#### 🗂️ File Management")
    
    if st.button("📂 Browse Files", use_container_width=True, type="primary"):
        st.switch_page("pages/file_manager.py")
    
    if st.button("📤 Upload Files", use_container_width=True):
        st.session_state["action"] = "upload"
        st.switch_page("pages/file_manager.py")
    
    if st.button("📥 Download Files", use_container_width=True):
        st.session_state["action"] = "download"
        st.switch_page("pages/file_manager.py")

with col_b:
    st.markdown("#### 🪣 Bucket Operations")
    
    if st.button("🔍 List Buckets", use_container_width=True, type="primary"):
        st.switch_page("pages/buckets.py")
    
    if st.button("➕ Create Bucket", use_container_width=True):
        st.session_state["action"] = "create"
        st.switch_page("pages/buckets.py")
    
    if st.button("⚙️ Configure Bucket", use_container_width=True):
        st.session_state["action"] = "configure"
        st.switch_page("pages/buckets.py")

with col_c:
    st.markdown("#### 📤 Batch Operations")
    
    if st.button("🔄 Sync Folders", use_container_width=True, type="primary"):
        st.switch_page("pages/transfers.py")
    
    if st.button("📦 Batch Upload", use_container_width=True):
        st.session_state["transfer_mode"] = "upload"
        st.switch_page("pages/transfers.py")
    
    if st.button("📦 Batch Download", use_container_width=True):
        st.session_state["transfer_mode"] = "download"
        st.switch_page("pages/transfers.py")

st.markdown("")
st.divider()

# ============================================================================
# RECENT ACTIVITY
# ============================================================================

st.markdown("### 🕐 Recent Activity")
st.caption("Quick access to recently accessed files and operations")
st.markdown("")

tab1, tab2 = st.tabs(["📤 Recent Uploads", "📥 Recent Downloads"])

with tab1:
    recent_uploads = st.session_state.get("recent_uploads", [])
    
    if recent_uploads:
        for idx, upload in enumerate(recent_uploads[:5]):  # Show last 5
            col_i, col_ii, col_iii = st.columns([3, 2, 1])
            
            with col_i:
                st.markdown(f"**{upload.get('file_name', 'Unknown')}**")
            
            with col_ii:
                st.caption(f"🪣 {upload.get('bucket', 'N/A')} / {upload.get('prefix', '')}")
            
            with col_iii:
                st.caption(upload.get('timestamp', 'N/A'))
    else:
        st.info("📭 No recent uploads. Upload files from the File Manager page.")

with tab2:
    recent_downloads = st.session_state.get("recent_downloads", [])
    
    if recent_downloads:
        for idx, download in enumerate(recent_downloads[:5]):
            col_i, col_ii, col_iii = st.columns([3, 2, 1])
            
            with col_i:
                st.markdown(f"**{download.get('file_name', 'Unknown')}**")
            
            with col_ii:
                st.caption(f"🪣 {download.get('bucket', 'N/A')}")
            
            with col_iii:
                st.caption(download.get('timestamp', 'N/A'))
    else:
        st.info("📭 No recent downloads. Download files from the File Manager page.")

st.markdown("")
st.divider()

# ============================================================================
# STORAGE STATISTICS (PLACEHOLDER)
# ============================================================================

st.markdown("### 📊 Storage Statistics")
st.caption("Overview of your storage usage")
st.markdown("")

# Placeholder for storage stats
col1, col2 = st.columns(2)

with col1:
    st.info("""
    **Storage statistics coming soon!**
    
    This section will display:
    - Total storage used
    - Storage by bucket
    - File type distribution
    - Growth trends
    """)

with col2:
    st.info("""
    **Analytics features planned:**
    
    - Cost analysis
    - Access patterns
    - Lifecycle optimization
    - Compliance reports
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("")
st.divider()

st.caption("""
💡 **Tip**: Use the sidebar to navigate between pages. The COS client initializes automatically.

🔧 **Configuration**: Update credentials in Settings page or use the CLI `cos configure` command.

📚 **Documentation**: Visit the [COS CLI Documentation](docs/README.md) for more information.
""")

# ============================================================================
# DEBUG PANEL (Development Only)
# ============================================================================

try:
    debug_mode = st.secrets.get("debug_mode", False)
except Exception:
    debug_mode = False

if debug_mode:
    with st.expander("🐛 Debug Information", expanded=False):
        st.json({
            "session_state": {
                "current_bucket": st.session_state.get("current_bucket"),
                "current_prefix": st.session_state.get("current_prefix"),
                "recent_uploads_count": len(st.session_state.get("recent_uploads", [])),
                "session_start": str(st.session_state.get("session_start_time")),
            },
            "cos_client": {
                "initialized": cos_client is not None,
                "type": str(type(cos_client)) if cos_client else None,
            }
        })

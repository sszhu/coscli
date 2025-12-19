"""Buckets Page - Manage COS buckets."""

import streamlit as st
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.src.page_utils import setup_page_simple
from ui.src.utils import get_cos_client, handle_error
from ui.components.status_indicators import render_empty_state, render_loading_spinner

# ============================================================================
# PAGE SETUP
# ============================================================================

setup_page_simple(
    title="Bucket Management",
    icon="🪣",
    page_id="buckets",
    caption="Create and configure COS buckets"
)

# Get COS client
cos_client = get_cos_client()

if not cos_client:
    st.error("❌ COS client not initialized. Please configure credentials in Settings.")
    st.stop()

# ============================================================================
# ACTIONS
# ============================================================================

col1, col2 = st.columns([2, 10])

with col1:
    if st.button("➕ Create Bucket", type="primary"):
        st.info("🚧 Bucket creation will be implemented in Phase 3")

with col2:
    if st.button("🔄 Refresh"):
        st.cache_resource.clear()
        st.rerun()

st.divider()

# ============================================================================
# BUCKET LIST
# ============================================================================

try:
    with st.spinner("Loading buckets..."):
        buckets = cos_client.list_buckets()
    
    if not buckets:
        render_empty_state(
            title="No Buckets Found",
            message="Create your first bucket to get started with COS storage.",
            icon="🪣",
        )
    else:
        st.markdown(f"### 📋 Buckets ({len(buckets)})")
        st.markdown("")
        
        # Display buckets in a table-like format
        for bucket in buckets:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    st.markdown(f"#### 🪣 {bucket['Name']}")
                
                with col2:
                    st.markdown(f"**Region:** {bucket.get('Location', 'N/A')}")
                
                with col3:
                    st.markdown(f"**Created:** {bucket.get('CreationDate', 'N/A')[:10]}")
                
                with col4:
                    if st.button("📂 Browse", key=f"browse_{bucket['Name']}"):
                        st.session_state.current_bucket = bucket['Name']
                        st.switch_page("ui/pages/file_manager.py")
                
                st.divider()

except Exception as e:
    handle_error(e, "Failed to load buckets")

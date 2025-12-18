"""Transfers Page - Batch upload/download operations."""

import streamlit as st
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.src.utils import (
    inject_global_styles,
    render_sidebar_navigation,
    get_cos_client,
)
from ui.components.status_indicators import render_empty_state

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Transfers - COS Data Manager",
    page_icon="📤",
    layout="wide"
)

inject_global_styles()

# ============================================================================
# SIDEBAR
# ============================================================================

render_sidebar_navigation(current_page="transfers")

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.title("📤 Batch Transfers")
st.caption("Upload, download, and sync multiple files")
st.markdown("")

# Tabs for different transfer types
tab1, tab2, tab3 = st.tabs(["📤 Batch Upload", "📥 Batch Download", "🔄 Sync"])

with tab1:
    st.markdown("### 📤 Batch Upload")
    st.info("🚧 Batch upload will be implemented in Phase 4")
    
    render_empty_state(
        title="Batch Upload Coming Soon",
        message="This feature will allow you to upload multiple files and folders at once.",
        icon="📤",
    )

with tab2:
    st.markdown("### 📥 Batch Download")
    st.info("🚧 Batch download will be implemented in Phase 4")
    
    render_empty_state(
        title="Batch Download Coming Soon",
        message="This feature will allow you to download multiple files at once.",
        icon="📥",
    )

with tab3:
    st.markdown("### 🔄 Sync")
    st.info("🚧 Sync functionality will be implemented in Phase 4")
    
    render_empty_state(
        title="Sync Coming Soon",
        message="This feature will allow you to sync local folders with COS buckets.",
        icon="🔄",
    )

"""Settings Page - Configure credentials and preferences."""

import streamlit as st
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.src.page_utils import setup_page_simple
from ui.src.utils import get_cos_client
from ui.src.config import DEFAULT_REGION, DEFAULT_BUCKET

# ============================================================================
# PAGE SETUP
# ============================================================================

setup_page_simple(
    title="Settings",
    icon="⚙️",
    page_id="settings",
    caption="Configure credentials and application preferences"
)

# Tabs for different settings
tab1, tab2, tab3 = st.tabs(["🔐 Credentials", "👤 Profiles", "🎨 Preferences"])

with tab1:
    st.markdown("### 🔐 COS Credentials")
    st.markdown("")
    
    st.info("""
    **Note:** This UI reads credentials from your COS CLI configuration.
    
    To configure credentials, use the CLI:
    ```bash
    python -m cos config
    ```
    
    Or manually edit: `~/.cos/credentials`
    """)
    
    st.divider()
    
    # Test connection
    st.markdown("#### 🔌 Test Connection")
    
    if st.button("🧪 Test COS Connection", type="primary"):
        with st.spinner("Testing connection..."):
            cos_client = get_cos_client(initialize=True)
            
            if cos_client:
                success, message = cos_client.test_connection()
                
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("❌ Failed to initialize COS client. Check your configuration.")
    
    st.divider()
    
    # Display current config (read-only)
    st.markdown("#### 📋 Current Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Default Region", value=DEFAULT_REGION, disabled=True)
    
    with col2:
        st.text_input("Default Bucket", value=DEFAULT_BUCKET or "Not set", disabled=True)

with tab2:
    st.markdown("### 👤 Configuration Profiles")
    st.info("🚧 Profile management will be implemented in Phase 5")
    
    st.markdown("""
    **Profiles** allow you to switch between different COS accounts or configurations.
    
    For now, the UI uses the `default` profile from your COS CLI configuration.
    """)

with tab3:
    st.markdown("### 🎨 UI Preferences")
    st.info("🚧 UI preferences will be implemented in Phase 5")
    
    st.markdown("**Coming soon:**")
    st.markdown("- Theme selection (Light/Dark)")
    st.markdown("- Default page size for file listings")
    st.markdown("- File type display preferences")
    st.markdown("- Notification settings")

st.divider()

# Help section
with st.expander("📚 Help & Documentation"):
    st.markdown("""
    ### Getting Started
    
    1. **Configure COS CLI** (if not already done):
       ```bash
       python -m cos config
       ```
    
    2. **Enter your credentials:**
       - Secret ID
       - Secret Key
       - Default Region
       - (Optional) Default Bucket
    
    3. **Test the connection** using the button above
    
    4. **Start using the UI!**
    
    ### Documentation
    
    - [Full Documentation](docs/ui/README_UI.md)
    - [Design Spec](docs/ui/UI_DESIGN.md)
    - [Quick Reference](docs/ui/QUICKREF.md)
    
    ### Troubleshooting
    
    If you're having connection issues:
    
    - Verify your credentials are correct
    - Check your internet connection
    - Ensure the region is correct
    - Review COS IAM permissions
    
    For more help, see [Troubleshooting Guide](docs/ui/README_UI.md#troubleshooting)
    """)

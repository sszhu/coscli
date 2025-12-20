"""Utility functions for COS Data Manager UI."""

from typing import Optional, Callable, Dict, Any
from pathlib import Path
import streamlit as st

# ============================================================================
# GLOBAL STYLES
# ============================================================================

def inject_global_styles():
    """Inject custom CSS styles into the Streamlit app."""
    css_path = Path(__file__).resolve().parent.parent / "static" / "styles" / "page.css"
    
    # Default styles if file doesn't exist
    default_css = """
    <style>
    /* Hide Streamlit branding */
    div[data-testid="stToolbar"] {display: none;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Hide Streamlit's automatic page navigation */
    [data-testid="stSidebarNav"] {display: none;}
    
    /* Layout adjustments */
    .block-container {
        padding-top: 1.8rem;
        max-width: 1400px;
    }
    
    /* Buttons - Tencent Blue theme */
    div.stButton > button,
    div.stDownloadButton > button {
        background-color: #006EFF !important;
        color: #ffffff !important;
        border: 2px solid #006EFF !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.2s ease !important;
    }
    
    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        background-color: #0052CC !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 110, 255, 0.3) !important;
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
    
    /* Tables */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 8px;
    }
    </style>
    """
    
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
    else:
        st.markdown(default_css, unsafe_allow_html=True)


# ============================================================================
# NAVIGATION
# ============================================================================

def render_sidebar_navigation(current_page: str = "home"):
    """
    Render the standard sidebar navigation for all pages.
    
    Args:
        current_page: Current active page identifier
    """
    with st.sidebar:
        # Logo section
        st.markdown("### 🗂️ COS Manager")
        st.caption("Tencent Cloud Object Storage")
        st.divider()
        
        # Main navigation
        st.markdown("#### 📋 Navigation")
        
        pages = [
            ("app.py", "🏠 Home", "home"),
            ("pages/file_manager.py", "🗂️ File Manager", "files"),
            ("pages/buckets.py", "🪣 Buckets", "buckets"),
            ("pages/transfers.py", "📤 Transfers", "transfers"),
        ]
        
        for page_path, label, page_id in pages:
            if current_page == page_id:
                st.markdown(f"**{label}** ←")
            else:
                st.page_link(page_path, label=label)
        
        st.divider()
        
        # Settings section
        st.markdown("#### ⚙️ Settings")
        st.page_link("pages/settings.py", label="🔧 Configuration")
        
        st.divider()
        
        # Help section
        st.caption("""
        💡 **Quick Tips:**
        - Navigate pages from sidebar
        - Upload via drag & drop
        - Use search to filter files
        """)


# ============================================================================
# COS CLIENT
# ============================================================================

@st.cache_resource(show_spinner=False)
def _create_cached_cos_client(profile: str = "default"):
    """
    Create a cached COS client instance.
    
    Args:
        profile: Configuration profile name
        
    Returns:
        WebCOSClient instance or None if initialization fails
    """
    try:
        # Import here to avoid circular dependencies
        from .cos_client_wrapper import WebCOSClient
        
        client = WebCOSClient(profile)
        return client
    except Exception as e:
        st.error(f"Failed to initialize COS client: {str(e)}")
        return None


def get_cos_client(initialize: bool = False, profile: str = "default"):
    """
    Get or initialize the COS client.
    
    Automatically initializes the COS client if it doesn't exist in session state.
    
    Args:
        initialize: If True, forces re-creation of the client
        profile: Configuration profile to use
        
    Returns:
        WebCOSClient instance or None
    """
    # Check if client needs initialization
    needs_init = (
        initialize or 
        "cos_client" not in st.session_state or
        st.session_state.get("cos_profile") != profile
    )
    
    if needs_init:
        st.session_state.cos_client = _create_cached_cos_client(profile)
        st.session_state.cos_profile = profile
    
    return st.session_state.get("cos_client")


# ============================================================================
# FORMATTING HELPERS
# ============================================================================

def format_size(bytes_size) -> str:
    """
    Format bytes into human-readable size.
    
    Args:
        bytes_size: Size in bytes (int or str)
        
    Returns:
        Formatted size string (e.g., "2.4 MB")
    """
    # Convert to int if string
    try:
        bytes_size = int(bytes_size)
    except (ValueError, TypeError):
        return "0 B"
    
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 ** 2:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 ** 3:
        return f"{bytes_size / (1024 ** 2):.1f} MB"
    else:
        return f"{bytes_size / (1024 ** 3):.2f} GB"


def format_datetime(dt) -> str:
    """
    Format datetime into relative or absolute string.
    
    Args:
        dt: Datetime object or ISO format string
        
    Returns:
        Formatted datetime string
    """
    from datetime import datetime, timedelta
    
    if not dt:
        return "N/A"
    
    # Parse string to datetime if needed
    if isinstance(dt, str):
        try:
            # Try ISO format first
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            try:
                # Try common datetime formats
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                    try:
                        dt = datetime.strptime(dt, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return dt  # Return original string if parsing fails
            except Exception:
                return dt
    
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt
    
    if diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}m ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days}d ago"
    else:
        return dt.strftime("%Y-%m-%d %H:%M")


def get_file_emoji(file_name: str) -> str:
    """
    Get emoji icon for file based on extension.
    
    Args:
        file_name: File name with extension
        
    Returns:
        Emoji string
    """
    from .config import FILE_EXTENSION_EMOJIS, FILE_EMOJI
    
    ext = Path(file_name).suffix.upper().lstrip('.')
    return FILE_EXTENSION_EMOJIS.get(ext, FILE_EMOJI)


# ============================================================================
# SESSION STATE HELPERS
# ============================================================================

def init_session_state(defaults: Dict[str, Any]):
    """
    Initialize session state with default values.
    
    Args:
        defaults: Dictionary of key-value pairs to initialize
    """
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_bucket_prefix_selector(on_change_callback: Optional[Callable] = None):
    """
    Render bucket and prefix selector with fallback for users without list permission.
    
    Uses selectbox if list_buckets() succeeds, otherwise uses text_input.
    Automatically uses DEFAULT_BUCKET and DEFAULT_PREFIX from config.
    
    Args:
        on_change_callback: Optional callback when bucket/prefix changes
        
    Returns:
        Tuple of (bucket, prefix)
    """
    from ui.src.config import DEFAULT_BUCKET, DEFAULT_PREFIX
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        cos_client = get_cos_client()
        bucket_changed = False
        
        if cos_client:
            # Try to list buckets (might fail if no permission)
            try:
                buckets = cos_client.list_buckets()
                bucket_names = [b['Name'] for b in buckets]
                
                if bucket_names:
                    # Use selectbox if we have bucket list
                    default_idx = 0
                    current = st.session_state.get('current_bucket', DEFAULT_BUCKET)
                    if current in bucket_names:
                        default_idx = bucket_names.index(current)
                    
                    selected_bucket = st.selectbox(
                        "🪣 Bucket",
                        options=bucket_names,
                        index=default_idx,
                        key="bucket_selector"
                    )
                else:
                    # Empty bucket list, use text input
                    selected_bucket = st.text_input(
                        "🪣 Bucket",
                        value=st.session_state.get('current_bucket', DEFAULT_BUCKET),
                        placeholder="my-bucket-name",
                        key="bucket_input"
                    )
            except Exception as e:
                # No permission to list buckets, use text input
                st.caption("⚠️ Using manual input (no list permission)")
                selected_bucket = st.text_input(
                    "🪣 Bucket",
                    value=st.session_state.get('current_bucket', DEFAULT_BUCKET),
                    placeholder="my-bucket-name",
                    key="bucket_input_fallback"
                )
            
            # Check if bucket changed
            if selected_bucket != st.session_state.get('current_bucket'):
                st.session_state.current_bucket = selected_bucket
                st.session_state.current_prefix = DEFAULT_PREFIX
                bucket_changed = True
        else:
            st.error("❌ COS not initialized. Configure in Settings.")
            return None, None
    
    with col2:
        new_prefix = st.text_input(
            "📂 Prefix (folder path)",
            value=st.session_state.get('current_prefix', DEFAULT_PREFIX),
            placeholder="data/experiments/",
            key="prefix_input"
        )
        
        prefix_changed = new_prefix != st.session_state.get('current_prefix')
        if prefix_changed:
            st.session_state.current_prefix = new_prefix
    
    # Show current location
    bucket = st.session_state.get('current_bucket', DEFAULT_BUCKET)
    prefix = st.session_state.get('current_prefix', DEFAULT_PREFIX)
    
    if bucket:
        st.info(f"📍 `cos://{bucket}/{prefix}`")
    
    # Trigger callback if changed
    if (bucket_changed or prefix_changed) and on_change_callback:
        on_change_callback()
    
    return bucket, prefix


def update_recent_activity(
    activity_type: str,
    item: Dict[str, Any],
    max_items: int = 10
):
    """
    Update recent activity in session state.
    
    Args:
        activity_type: 'upload' or 'download'
        item: Activity item dictionary
        max_items: Maximum number of items to keep
    """
    key = f"recent_{activity_type}s"
    
    if key not in st.session_state:
        st.session_state[key] = []
    
    # Add timestamp if not present
    if 'timestamp' not in item:
        from datetime import datetime
        item['timestamp'] = datetime.now().strftime("%H:%M:%S")
    
    # Prepend new item
    st.session_state[key].insert(0, item)
    
    # Trim to max items
    st.session_state[key] = st.session_state[key][:max_items]


# ============================================================================
# VALIDATION
# ============================================================================

def validate_bucket_name(bucket_name: str) -> tuple[bool, str]:
    """
    Validate bucket name according to COS rules.
    
    Args:
        bucket_name: Bucket name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not bucket_name:
        return False, "Bucket name cannot be empty"
    
    if len(bucket_name) < 3 or len(bucket_name) > 63:
        return False, "Bucket name must be 3-63 characters"
    
    if not bucket_name[0].isalnum() or not bucket_name[-1].isalnum():
        return False, "Bucket name must start and end with letter or number"
    
    # Check for valid characters
    valid_chars = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    if not set(bucket_name.lower()).issubset(valid_chars):
        return False, "Bucket name can only contain lowercase letters, numbers, and hyphens"
    
    return True, ""


def validate_object_key(key: str) -> tuple[bool, str]:
    """
    Validate object key.
    
    Args:
        key: Object key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not key:
        return False, "Object key cannot be empty"
    
    if len(key) > 1024:
        return False, "Object key must be less than 1024 characters"
    
    return True, ""


# ============================================================================
# ERROR HANDLING
# ============================================================================

def handle_error(error: Exception, context: str = ""):
    """
    Display error message in Streamlit UI.
    
    Args:
        error: Exception object
        context: Optional context message
    """
    error_msg = f"{context}: {str(error)}" if context else str(error)
    st.error(f"❌ {error_msg}")
    
    # Show detailed error in expander for debugging
    with st.expander("🐛 Error Details"):
        st.code(str(error))
        st.caption("If this error persists, check your credentials or contact support.")


# ============================================================================
# PROGRESS TRACKING
# ============================================================================

class ProgressTracker:
    """Simple progress tracker for uploads/downloads."""
    
    def __init__(self, total: int, label: str = "Progress"):
        self.total = total
        self.current = 0
        self.label = label
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
    
    def update(self, increment: int = 1):
        """Update progress."""
        self.current += increment
        progress = min(self.current / self.total, 1.0)
        self.progress_bar.progress(progress)
        self.status_text.text(f"{self.label}: {self.current}/{self.total}")
    
    def complete(self):
        """Mark as complete and clean up."""
        self.progress_bar.empty()
        self.status_text.empty()


# ============================================================================
# RERUN HELPER
# ============================================================================

def trigger_refresh():
    """Trigger a rerun of the Streamlit app."""
    rerun = getattr(st, "experimental_rerun", None) or getattr(st, "rerun", None)
    if callable(rerun):
        rerun()

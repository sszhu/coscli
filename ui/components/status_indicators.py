"""Status indicators and loading states components."""

import streamlit as st
from typing import Optional


def render_connection_status(
    is_connected: bool,
    message: str = "",
    show_details: bool = True,
) -> None:
    """
    Render connection status indicator.
    
    Args:
        is_connected: Whether connection is successful
        message: Optional status message
        show_details: Whether to show expandable details
    """
    if is_connected:
        icon = "🟢"
        status_text = "Connected"
        status_type = "success"
        default_msg = "Successfully connected to COS"
    else:
        icon = "🔴"
        status_text = "Disconnected"
        status_type = "error"
        default_msg = "Not connected to COS. Check your credentials."
    
    display_message = message or default_msg
    
    if status_type == "success":
        st.success(f"{icon} **{status_text}** - {display_message}")
    else:
        st.error(f"{icon} **{status_text}** - {display_message}")
    
    if show_details and not is_connected:
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            **Common issues:**
            1. **Invalid credentials** - Check your Secret ID and Secret Key
            2. **Network issues** - Verify internet connection
            3. **Region mismatch** - Ensure correct region is configured
            4. **Permission denied** - Check IAM permissions
            
            **Next steps:**
            - Go to Settings → Configuration to update credentials
            - Test connection after updating
            - Check the [documentation](docs/ui/README_UI.md) for setup help
            """)


def render_loading_spinner(message: str = "Loading...") -> None:
    """
    Render a loading spinner with message.
    
    Args:
        message: Loading message to display
    """
    with st.spinner(message):
        pass


def render_empty_state(
    title: str,
    message: str,
    icon: str = "📭",
    action_label: Optional[str] = None,
    action_callback: Optional[callable] = None,
) -> None:
    """
    Render an empty state placeholder.
    
    Args:
        title: Empty state title
        message: Descriptive message
        icon: Emoji icon
        action_label: Optional action button label
        action_callback: Optional callback for action button
    """
    st.markdown(
        f"""
        <div style="text-align: center; padding: 60px 20px; color: #8C8C8C;">
            <div style="font-size: 64px; margin-bottom: 20px;">{icon}</div>
            <h3 style="color: #4A4A4A; margin-bottom: 10px;">{title}</h3>
            <p style="font-size: 16px;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if action_label and action_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(action_label, type="primary", use_container_width=True):
                action_callback()


def render_status_banner(
    status_type: str,
    message: str,
    dismissible: bool = False,
) -> None:
    """
    Render a status banner.
    
    Args:
        status_type: Type of status ('info', 'success', 'warning', 'error')
        message: Status message
        dismissible: Whether the banner can be dismissed
    """
    status_functions = {
        'info': st.info,
        'success': st.success,
        'warning': st.warning,
        'error': st.error,
    }
    
    func = status_functions.get(status_type, st.info)
    
    if dismissible:
        # Store dismissal state
        banner_key = f"banner_{hash(message)}"
        if banner_key not in st.session_state:
            st.session_state[banner_key] = True
        
        if st.session_state[banner_key]:
            col1, col2 = st.columns([20, 1])
            with col1:
                func(message)
            with col2:
                if st.button("✕", key=f"dismiss_{banner_key}"):
                    st.session_state[banner_key] = False
                    st.rerun()
    else:
        func(message)


def render_metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    icon: str = "📊",
) -> None:
    """
    Render a metric card.
    
    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta/change indicator
        icon: Emoji icon
    """
    st.markdown(
        f"""
        <div class="metric-card">
            <div style="font-size: 32px; margin-bottom: 8px;">{icon}</div>
            <div style="font-size: 24px; font-weight: 600; color: #1A1A1A; margin-bottom: 4px;">
                {value}
            </div>
            <div style="font-size: 14px; color: #8C8C8C; margin-bottom: 4px;">
                {label}
            </div>
            {f'<div style="font-size: 12px; color: #006EFF;">{delta}</div>' if delta else ''}
        </div>
        """,
        unsafe_allow_html=True
    )

"""Action buttons and action bar components."""

import streamlit as st
from typing import Optional, Callable, List, Dict


def render_action_button(
    label: str,
    icon: str = "",
    on_click: Optional[Callable] = None,
    button_type: str = "secondary",
    disabled: bool = False,
    use_container_width: bool = False,
    key: Optional[str] = None,
) -> bool:
    """
    Render an action button.
    
    Args:
        label: Button label
        icon: Optional emoji icon
        on_click: Callback when clicked
        button_type: Button type ('primary', 'secondary')
        disabled: Whether button is disabled
        use_container_width: Whether to use full container width
        key: Unique key for button
        
    Returns:
        Whether button was clicked
    """
    button_label = f"{icon} {label}" if icon else label
    
    clicked = st.button(
        button_label,
        type=button_type,
        disabled=disabled,
        use_container_width=use_container_width,
        key=key or f"btn_{label.replace(' ', '_')}",
    )
    
    if clicked and on_click:
        on_click()
    
    return clicked


def render_action_bar(
    actions: List[Dict],
    align: str = "left",
) -> Dict[str, bool]:
    """
    Render a horizontal action bar with multiple buttons.
    
    Args:
        actions: List of action dictionaries with keys:
            - label: Button label
            - icon: Optional emoji icon
            - on_click: Optional callback
            - type: Button type ('primary' or 'secondary')
            - disabled: Whether disabled
            - key: Unique key
        align: Alignment ('left', 'center', 'right')
        
    Returns:
        Dictionary of action keys to click status
    """
    num_actions = len(actions)
    
    if align == "center":
        cols = st.columns([1] + [2] * num_actions + [1])
        cols = cols[1:-1]
    elif align == "right":
        cols = st.columns([3] + [1] * num_actions)
        cols = cols[1:]
    else:  # left
        cols = st.columns(num_actions)
    
    results = {}
    
    for col, action in zip(cols, actions):
        with col:
            clicked = render_action_button(
                label=action.get('label', ''),
                icon=action.get('icon', ''),
                on_click=action.get('on_click'),
                button_type=action.get('type', 'secondary'),
                disabled=action.get('disabled', False),
                use_container_width=True,
                key=action.get('key'),
            )
            results[action.get('key', action.get('label', ''))] = clicked
    
    return results


def render_confirm_dialog(
    title: str,
    message: str,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
    danger: bool = False,
) -> Optional[bool]:
    """
    Render a confirmation dialog.
    
    Args:
        title: Dialog title
        message: Confirmation message
        confirm_label: Confirm button label
        cancel_label: Cancel button label
        danger: Whether this is a dangerous action (red button)
        
    Returns:
        True if confirmed, False if cancelled, None if no action
    """
    st.markdown(f"### {title}")
    st.warning(message)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button(
            confirm_label,
            type="primary" if not danger else "secondary",
            use_container_width=True,
            key="confirm_btn",
        ):
            return True
    
    with col2:
        if st.button(
            cancel_label,
            use_container_width=True,
            key="cancel_btn",
        ):
            return False
    
    return None


def render_download_button(
    label: str,
    data: bytes,
    file_name: str,
    mime_type: str = "application/octet-stream",
    icon: str = "📥",
    use_container_width: bool = False,
) -> bool:
    """
    Render a download button.
    
    Args:
        label: Button label
        data: File data as bytes
        file_name: Name for downloaded file
        mime_type: MIME type
        icon: Optional emoji icon
        use_container_width: Whether to use full container width
        
    Returns:
        Whether button was clicked
    """
    button_label = f"{icon} {label}" if icon else label
    
    clicked = st.download_button(
        label=button_label,
        data=data,
        file_name=file_name,
        mime=mime_type,
        use_container_width=use_container_width,
    )
    
    return clicked


def render_upload_button(
    label: str = "Upload Files",
    accept_multiple_files: bool = True,
    accepted_types: Optional[List[str]] = None,
    key: Optional[str] = None,
):
    """
    Render a file upload button.
    
    Args:
        label: Upload button label
        accept_multiple_files: Whether to accept multiple files
        accepted_types: List of accepted file types (e.g., ['.csv', '.json'])
        key: Unique key
        
    Returns:
        Uploaded file(s) or None
    """
    uploaded = st.file_uploader(
        label=label,
        accept_multiple_files=accept_multiple_files,
        type=accepted_types,
        key=key or "file_uploader",
    )
    
    return uploaded


def render_search_bar(
    placeholder: str = "Search...",
    icon: str = "🔍",
    on_change: Optional[Callable] = None,
    key: Optional[str] = None,
) -> str:
    """
    Render a search input bar.
    
    Args:
        placeholder: Placeholder text
        icon: Search icon
        on_change: Callback when search changes
        key: Unique key
        
    Returns:
        Search query string
    """
    query = st.text_input(
        label=f"{icon} Search",
        placeholder=placeholder,
        label_visibility="collapsed",
        key=key or "search_bar",
        on_change=on_change,
    )
    
    return query


def render_filter_panel(
    filters: Dict[str, List[str]],
    selected_filters: Dict[str, str],
    on_change: Optional[Callable] = None,
) -> Dict[str, str]:
    """
    Render a filter panel with multiple dropdowns.
    
    Args:
        filters: Dictionary of filter_name -> options list
        selected_filters: Dictionary of filter_name -> selected_value
        on_change: Callback when any filter changes
        
    Returns:
        Updated selected_filters dictionary
    """
    cols = st.columns(len(filters))
    
    updated_filters = {}
    
    for col, (filter_name, options) in zip(cols, filters.items()):
        with col:
            selected = st.selectbox(
                label=filter_name,
                options=["All"] + options,
                index=0 if selected_filters.get(filter_name) is None 
                      else options.index(selected_filters[filter_name]) + 1,
                key=f"filter_{filter_name}",
            )
            
            updated_filters[filter_name] = None if selected == "All" else selected
    
    if on_change and updated_filters != selected_filters:
        on_change(updated_filters)
    
    return updated_filters

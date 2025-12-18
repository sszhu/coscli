"""File display components for file lists and trees."""

import streamlit as st
from typing import List, Dict, Optional, Callable
from pathlib import Path


def render_file_row(
    file: Dict,
    selectable: bool = True,
    selected: bool = False,
    on_select: Optional[Callable] = None,
    on_download: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
    get_file_emoji: Optional[Callable] = None,
    format_size: Optional[Callable] = None,
    format_datetime: Optional[Callable] = None,
) -> bool:
    """
    Render a single file row with actions.
    
    Args:
        file: File dictionary with keys (key, name, size, last_modified)
        selectable: Whether file can be selected
        selected: Whether file is currently selected
        on_select: Callback when selection changes
        on_download: Callback for download action
        on_delete: Callback for delete action
        get_file_emoji: Function to get emoji for file
        format_size: Function to format file size
        format_datetime: Function to format datetime
        
    Returns:
        Whether the file is selected after rendering
    """
    # Default formatters
    if not get_file_emoji:
        get_file_emoji = lambda name: "📄"
    if not format_size:
        format_size = lambda size: f"{size} bytes"
    if not format_datetime:
        format_datetime = lambda dt: str(dt)
    
    # Create columns
    if selectable:
        col_check, col_icon, col_name, col_size, col_date, col_actions = st.columns([0.5, 0.5, 4, 1.5, 1.5, 1.5])
    else:
        col_icon, col_name, col_size, col_date, col_actions = st.columns([0.5, 4, 1.5, 1.5, 1.5])
    
    # Checkbox
    if selectable:
        with col_check:
            is_selected = st.checkbox(
                label="",
                value=selected,
                key=f"select_{file['key']}",
                label_visibility="collapsed",
            )
            if on_select and is_selected != selected:
                on_select(file, is_selected)
    else:
        is_selected = selected
    
    # Icon and name
    with col_icon:
        st.markdown(f"<div style='font-size: 24px;'>{get_file_emoji(file['name'])}</div>", unsafe_allow_html=True)
    
    with col_name:
        st.markdown(f"**{file['name']}**")
        if 'key' in file and file['key'] != file['name']:
            st.caption(f"Path: {file['key']}")
    
    # Size
    with col_size:
        st.text(format_size(file.get('size', 0)))
    
    # Date
    with col_date:
        if 'last_modified' in file:
            st.text(format_datetime(file['last_modified']))
    
    # Actions
    with col_actions:
        action_col1, action_col2 = st.columns(2)
        
        with action_col1:
            if on_download and st.button("📥", key=f"dl_{file['key']}", help="Download"):
                on_download(file)
        
        with action_col2:
            if on_delete and st.button("🗑️", key=f"del_{file['key']}", help="Delete"):
                on_delete(file)
    
    return is_selected


def render_file_list_table(
    files: List[Dict],
    selectable: bool = True,
    selected_keys: Optional[List[str]] = None,
    on_select_change: Optional[Callable] = None,
    on_download: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
    get_file_emoji: Optional[Callable] = None,
    format_size: Optional[Callable] = None,
    format_datetime: Optional[Callable] = None,
    empty_message: str = "No files found",
) -> List[str]:
    """
    Render a table of files.
    
    Args:
        files: List of file dictionaries
        selectable: Whether files can be selected
        selected_keys: List of currently selected file keys
        on_select_change: Callback when selection changes
        on_download: Callback for download action
        on_delete: Callback for delete action
        get_file_emoji: Function to get emoji for file
        format_size: Function to format file size
        format_datetime: Function to format datetime
        empty_message: Message to show when no files
        
    Returns:
        List of selected file keys
    """
    if not files:
        st.info(f"📭 {empty_message}")
        return []
    
    selected_keys = selected_keys or []
    
    # Header row
    if selectable:
        col_check, col_icon, col_name, col_size, col_date, col_actions = st.columns([0.5, 0.5, 4, 1.5, 1.5, 1.5])
        
        with col_check:
            select_all = st.checkbox("", key="select_all_header", label_visibility="collapsed")
            if select_all:
                selected_keys = [f['key'] for f in files]
            else:
                if len(selected_keys) == len(files):
                    selected_keys = []
    else:
        col_icon, col_name, col_size, col_date, col_actions = st.columns([0.5, 4, 1.5, 1.5, 1.5])
    
    with col_name:
        st.markdown("**Name**")
    with col_size:
        st.markdown("**Size**")
    with col_date:
        st.markdown("**Modified**")
    with col_actions:
        st.markdown("**Actions**")
    
    st.divider()
    
    # File rows
    new_selected = []
    for file in files:
        is_selected = file['key'] in selected_keys
        
        result = render_file_row(
            file=file,
            selectable=selectable,
            selected=is_selected,
            on_select=lambda f, sel: on_select_change(f, sel) if on_select_change else None,
            on_download=on_download,
            on_delete=on_delete,
            get_file_emoji=get_file_emoji,
            format_size=format_size,
            format_datetime=format_datetime,
        )
        
        if result:
            new_selected.append(file['key'])
    
    return new_selected


def render_folder_tree(
    folders: List[str],
    current_prefix: str = "",
    on_folder_click: Optional[Callable] = None,
    expanded_folders: Optional[List[str]] = None,
) -> None:
    """
    Render a folder tree navigation.
    
    Args:
        folders: List of folder paths
        current_prefix: Currently selected prefix
        on_folder_click: Callback when folder is clicked
        expanded_folders: List of expanded folder paths
    """
    if not folders:
        st.info("📁 No folders found")
        return
    
    expanded_folders = expanded_folders or []
    
    st.markdown("### 📁 Folders")
    
    # Build tree structure
    tree = {}
    for folder in folders:
        parts = folder.rstrip('/').split('/')
        current = tree
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]
    
    # Render tree
    def render_tree_node(name: str, children: Dict, depth: int = 0, prefix: str = ""):
        indent = "  " * depth
        full_path = f"{prefix}{name}/" if prefix or name else ""
        
        is_expanded = full_path in expanded_folders
        is_current = full_path == current_prefix
        
        # Render node
        col1, col2 = st.columns([10, 1])
        
        with col1:
            icon = "▼" if is_expanded else "▶"
            style = "font-weight: bold; color: #006EFF;" if is_current else ""
            
            if st.button(
                f"{indent}{icon} 📁 {name}",
                key=f"folder_{full_path}",
                use_container_width=True,
            ):
                if on_folder_click:
                    on_folder_click(full_path)
        
        # Render children if expanded
        if is_expanded and children:
            for child_name, child_children in children.items():
                render_tree_node(child_name, child_children, depth + 1, full_path)
    
    for name, children in tree.items():
        render_tree_node(name, children)


def render_breadcrumb_navigation(
    current_path: str,
    on_navigate: Optional[Callable] = None,
) -> None:
    """
    Render breadcrumb navigation for current path.
    
    Args:
        current_path: Current path/prefix
        on_navigate: Callback when breadcrumb is clicked
    """
    if not current_path:
        st.markdown("📍 **/** (root)")
        return
    
    parts = current_path.rstrip('/').split('/')
    
    breadcrumbs = ["🏠"]
    path_parts = [""]
    
    for part in parts:
        breadcrumbs.append(part)
        path_parts.append(f"{path_parts[-1]}{part}/")
    
    # Render as clickable links
    cols = st.columns(len(breadcrumbs))
    
    for idx, (breadcrumb, path) in enumerate(zip(breadcrumbs, path_parts)):
        with cols[idx]:
            if st.button(breadcrumb, key=f"breadcrumb_{idx}"):
                if on_navigate:
                    on_navigate(path)

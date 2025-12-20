"""Reusable UI components for pages."""

import streamlit as st
from typing import Dict, List, Callable, Optional


def render_confirmation_dialog(
    message: str,
    on_confirm: Callable,
    on_cancel: Callable,
    confirm_label: str = "✅ Confirm",
    cancel_label: str = "❌ Cancel",
    warning: bool = True
):
    """Render a confirmation dialog with confirm/cancel buttons.
    
    Args:
        message: Message to display
        on_confirm: Callback when confirmed
        on_cancel: Callback when cancelled
        confirm_label: Label for confirm button
        cancel_label: Label for cancel button
        warning: Whether to style as warning
    """
    with st.container():
        if warning:
            st.warning(message)
        else:
            st.info(message)
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button(confirm_label, type="primary"):
                on_confirm()
        
        with col2:
            if st.button(cancel_label):
                on_cancel()
        
        st.divider()


def render_modal_dialog(
    title: str,
    input_config: Dict,
    on_submit: Callable,
    on_cancel: Callable,
    submit_label: str = "✅ Submit",
    cancel_label: str = "❌ Cancel",
):
    """Render a modal dialog with input and action buttons.
    
    Args:
        title: Dialog title
        input_config: Dict with input configuration
            - type: 'text', 'select', 'file', etc.
            - label: Input label
            - kwargs: Additional input kwargs
        on_submit: Callback with input value
        on_cancel: Callback when cancelled
        submit_label: Label for submit button
        cancel_label: Label for cancel button
    """
    with st.container():
        st.markdown(f"### {title}")
        
        input_type = input_config.get('type', 'text')
        label = input_config.get('label', '')
        kwargs = input_config.get('kwargs', {})
        
        # Render appropriate input
        value = None
        if input_type == 'text':
            value = st.text_input(label, **kwargs)
        elif input_type == 'select':
            value = st.selectbox(label, **kwargs)
        elif input_type == 'file':
            value = st.file_uploader(label, **kwargs)
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button(submit_label, type="primary", disabled=not value):
                on_submit(value)
        
        with col2:
            if st.button(cancel_label):
                on_cancel()
        
        st.divider()


def render_search_filter_bar(
    search_value: str,
    filter_options: List[str],
    filter_value: str,
    sort_options: Dict[str, tuple],
    sort_value: str,
    on_search_change: Callable,
    on_filter_change: Callable,
    on_sort_change: Callable,
):
    """Render search, filter, and sort controls.
    
    Args:
        search_value: Current search query
        filter_options: List of filter type options
        filter_value: Current filter selection
        sort_options: Dict mapping display names to (sort_by, sort_order) tuples
        sort_value: Current sort selection
        on_search_change: Callback for search changes
        on_filter_change: Callback for filter changes
        on_sort_change: Callback for sort changes
    """
    col1, col2, col3 = st.columns([3, 2, 2])
    
    with col1:
        search = st.text_input(
            "Search",
            value=search_value,
            placeholder="filename...",
            label_visibility="collapsed",
        )
        if search != search_value:
            on_search_change(search)
    
    with col2:
        filter_type = st.selectbox("Type", options=filter_options)
        if filter_type != filter_value:
            on_filter_change(filter_type)
    
    with col3:
        sort_display = st.selectbox("Sort", options=list(sort_options.keys()))
        if sort_display != sort_value:
            on_sort_change(sort_display)


def render_pagination_controls(
    page_num: int,
    total_pages: int,
    on_page_change: Callable,
):
    """Render pagination controls.
    
    Args:
        page_num: Current page number
        total_pages: Total number of pages
        on_page_change: Callback with new page number
    """
    if total_pages <= 1:
        return
    
    st.markdown("")
    c1, c2, c3, c4, c5 = st.columns([1, 1, 2, 1, 1])
    
    with c1:
        if st.button("⏮️", disabled=(page_num == 1)):
            on_page_change(1)
    
    with c2:
        if st.button("◀️", disabled=(page_num == 1)):
            on_page_change(max(1, page_num - 1))
    
    with c3:
        st.markdown(
            f"<div style='text-align:center'>Page {page_num}/{total_pages}</div>",
            unsafe_allow_html=True
        )
    
    with c4:
        if st.button("▶️", disabled=(page_num == total_pages)):
            on_page_change(min(total_pages, page_num + 1))
    
    with c5:
        if st.button("⏭️", disabled=(page_num == total_pages)):
            on_page_change(total_pages)


def render_file_table(
    files: List[Dict],
    selected_keys: List[str],
    on_selection_change: Callable,
    on_download: Optional[Callable] = None,
    on_url: Optional[Callable] = None,
    show_actions: bool = True,
):
    """Render file list as a table with checkboxes and actions.
    
    Args:
        files: List of file dictionaries
        selected_keys: List of selected file keys
        on_selection_change: Callback with updated selection
        on_download: Optional download callback
        on_url: Optional URL generation callback
        show_actions: Whether to show action buttons
    """
    from ui.src.utils import format_size, format_datetime, get_file_emoji
    
    # Header
    if show_actions:
        c1, c2, c3, c4, c5 = st.columns([0.5, 4, 1.5, 1.5, 2])
    else:
        c1, c2, c3, c4 = st.columns([0.5, 4, 1.5, 1.5])
    
    with c1:
        select_all = st.checkbox("Select All", key="sel_all", label_visibility="collapsed")
        if select_all and len(selected_keys) != len(files):
            on_selection_change([f['key'] for f in files])
        elif not select_all and len(selected_keys) == len(files):
            on_selection_change([])
    
    with c2:
        st.markdown("**Name**")
    with c3:
        st.markdown("**Size**")
    with c4:
        st.markdown("**Modified**")
    if show_actions:
        with c5:
            st.markdown("**Actions**")
    
    st.divider()
    
    # Rows
    for file in files:
        if show_actions:
            c1, c2, c3, c4, c5 = st.columns([0.5, 4, 1.5, 1.5, 2])
        else:
            c1, c2, c3, c4 = st.columns([0.5, 4, 1.5, 1.5])
        
        with c1:
            is_sel = file['key'] in selected_keys
            checked = st.checkbox(
                "Select",
                value=is_sel,
                key=f"c_{file['key']}",
                label_visibility="collapsed"
            )
            
            if checked and not is_sel:
                new_selection = selected_keys + [file['key']]
                on_selection_change(new_selection)
            elif not checked and is_sel:
                new_selection = [k for k in selected_keys if k != file['key']]
                on_selection_change(new_selection)
        
        with c2:
            emoji = get_file_emoji(file['name'])
            st.markdown(f"{emoji} **{file['name']}**")
        
        with c3:
            st.text(format_size(file.get('size', 0)))
        
        with c4:
            if 'last_modified' in file:
                st.text(format_datetime(file['last_modified']))
        
        if show_actions:
            with c5:
                a1, a2 = st.columns(2)
                
                with a1:
                    if on_download and st.button("📥", key=f"dl_{file['key']}", help="Download"):
                        on_download(file)
                
                with a2:
                    if on_url and st.button("🔗", key=f"url_{file['key']}", help="URL"):
                        on_url(file)


def render_bulk_actions(
    selected_count: int,
    on_clear: Callable,
    additional_actions: Optional[Dict[str, Callable]] = None,
):
    """Render bulk actions bar for selected items.
    
    Args:
        selected_count: Number of selected items
        on_clear: Callback to clear selection
        additional_actions: Optional dict of {label: callback}
    """
    if selected_count == 0:
        return
    
    st.markdown("---")
    st.markdown(f"### ✅ {selected_count} selected")
    
    num_actions = 1 + (len(additional_actions) if additional_actions else 0)
    cols = st.columns(num_actions + 3)  # Extra cols for spacing
    
    with cols[0]:
        if st.button("❌ Clear", use_container_width=True):
            on_clear()
    
    if additional_actions:
        for idx, (label, callback) in enumerate(additional_actions.items(), 1):
            with cols[idx]:
                if st.button(label, use_container_width=True):
                    callback()

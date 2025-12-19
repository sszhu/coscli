"""Base page utilities for common page setup patterns."""

import streamlit as st
from pathlib import Path
import sys
from typing import Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.src.utils import (
    inject_global_styles,
    render_sidebar_navigation,
)


class BasePage:
    """Base class for COS UI pages."""
    
    def __init__(
        self,
        title: str,
        icon: str,
        page_id: str,
        caption: Optional[str] = None,
        layout: str = "wide",
    ):
        """Initialize a page with common setup.
        
        Args:
            title: Page title
            icon: Page icon/emoji
            page_id: Unique page identifier for navigation
            caption: Optional subtitle/description
            layout: Streamlit page layout ('wide' or 'centered')
        """
        self.title = title
        self.icon = icon
        self.page_id = page_id
        self.caption = caption
        self.layout = layout
        
        self._setup_page()
    
    def _setup_page(self):
        """Set up page configuration and styles."""
        st.set_page_config(
            page_title=f"{self.title} - COS Data Manager",
            page_icon=self.icon,
            layout=self.layout
        )
        
        inject_global_styles()
        render_sidebar_navigation(current_page=self.page_id)
    
    def render_header(self):
        """Render page header with title and caption."""
        st.title(f"{self.icon} {self.title}")
        if self.caption:
            st.caption(self.caption)
        st.markdown("")
    
    def render_action_bar(self, actions: dict):
        """Render action buttons in a row.
        
        Args:
            actions: Dict mapping button labels to callables
                    Format: {label: (callback, kwargs)}
        """
        cols = st.columns(len(actions))
        
        for col, (label, config) in zip(cols, actions.items()):
            with col:
                callback = config.get('callback')
                kwargs = config.get('kwargs', {})
                
                if st.button(label, use_container_width=True, **kwargs):
                    if callback:
                        callback()


def setup_page_simple(
    title: str,
    icon: str,
    page_id: str,
    caption: Optional[str] = None,
    layout: str = "wide"
):
    """Quick setup for simple pages without class instantiation.
    
    Args:
        title: Page title
        icon: Page icon/emoji
        page_id: Unique page identifier
        caption: Optional subtitle
        layout: Page layout
    """
    st.set_page_config(
        page_title=f"{title} - COS Data Manager",
        page_icon=icon,
        layout=layout
    )
    
    inject_global_styles()
    render_sidebar_navigation(current_page=page_id)
    
    st.title(f"{icon} {title}")
    if caption:
        st.caption(caption)
    st.markdown("")

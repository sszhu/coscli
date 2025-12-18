"""Progress tracking components."""

import streamlit as st
from typing import Optional
from datetime import datetime, timedelta


class ProgressBar:
    """Simple progress bar for single operations."""
    
    def __init__(
        self,
        total: int,
        label: str = "Progress",
        show_percentage: bool = True,
        show_count: bool = True,
    ):
        """
        Initialize progress bar.
        
        Args:
            total: Total number of items/bytes
            label: Progress label
            show_percentage: Whether to show percentage
            show_count: Whether to show count (current/total)
        """
        self.total = total
        self.current = 0
        self.label = label
        self.show_percentage = show_percentage
        self.show_count = show_count
        self.start_time = datetime.now()
        
        # Create UI elements
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        
        self._update_display()
    
    def update(self, increment: int = 1):
        """
        Update progress.
        
        Args:
            increment: Amount to increment (default 1)
        """
        self.current = min(self.current + increment, self.total)
        self._update_display()
    
    def set_progress(self, current: int):
        """
        Set absolute progress value.
        
        Args:
            current: Current progress value
        """
        self.current = min(current, self.total)
        self._update_display()
    
    def _update_display(self):
        """Update the progress bar and status text."""
        progress = self.current / self.total if self.total > 0 else 0
        self.progress_bar.progress(progress)
        
        # Build status text
        parts = [self.label]
        
        if self.show_percentage:
            parts.append(f"{progress * 100:.1f}%")
        
        if self.show_count:
            parts.append(f"({self.current}/{self.total})")
        
        # Add ETA
        if self.current > 0 and self.current < self.total:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            rate = self.current / elapsed
            remaining = (self.total - self.current) / rate
            eta = str(timedelta(seconds=int(remaining)))
            parts.append(f"ETA: {eta}")
        
        self.status_text.text(" | ".join(parts))
    
    def complete(self, success_message: Optional[str] = None):
        """
        Mark progress as complete and clean up.
        
        Args:
            success_message: Optional success message to display
        """
        self.current = self.total
        self._update_display()
        
        if success_message:
            self.status_text.success(success_message)
        
        # Clean up after a moment
        import time
        time.sleep(1)
        self.progress_bar.empty()
        if not success_message:
            self.status_text.empty()
    
    def error(self, error_message: str):
        """
        Mark progress as failed.
        
        Args:
            error_message: Error message to display
        """
        self.status_text.error(f"❌ {error_message}")
        self.progress_bar.empty()


class BatchProgress:
    """Progress tracker for batch operations with detailed stats."""
    
    def __init__(
        self,
        total_items: int,
        operation_name: str = "Processing",
    ):
        """
        Initialize batch progress tracker.
        
        Args:
            total_items: Total number of items to process
            operation_name: Name of the operation
        """
        self.total_items = total_items
        self.operation_name = operation_name
        self.completed = 0
        self.failed = 0
        self.current_item = ""
        self.start_time = datetime.now()
        self.errors = []
        
        # Create UI elements
        st.markdown(f"### {operation_name}")
        self.progress_bar = st.progress(0)
        self.status_container = st.container()
        self.error_container = st.expander("⚠️ Errors", expanded=False)
        
        self._update_display()
    
    def update_current(self, item_name: str):
        """
        Update current item being processed.
        
        Args:
            item_name: Name of current item
        """
        self.current_item = item_name
        self._update_display()
    
    def mark_success(self, item_name: str = ""):
        """
        Mark an item as successfully processed.
        
        Args:
            item_name: Name of the item
        """
        self.completed += 1
        if item_name:
            self.current_item = item_name
        self._update_display()
    
    def mark_failure(self, item_name: str, error: str):
        """
        Mark an item as failed.
        
        Args:
            item_name: Name of the item
            error: Error message
        """
        self.failed += 1
        self.errors.append(f"{item_name}: {error}")
        self._update_display()
    
    def _update_display(self):
        """Update the display."""
        total_processed = self.completed + self.failed
        progress = total_processed / self.total_items if self.total_items > 0 else 0
        self.progress_bar.progress(progress)
        
        # Calculate stats
        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = total_processed / elapsed if elapsed > 0 else 0
        remaining_items = self.total_items - total_processed
        eta_seconds = remaining_items / rate if rate > 0 else 0
        eta = str(timedelta(seconds=int(eta_seconds)))
        
        # Update status
        with self.status_container:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Progress",
                    f"{total_processed}/{self.total_items}",
                    f"{progress * 100:.1f}%"
                )
            
            with col2:
                st.metric(
                    "✅ Succeeded",
                    self.completed,
                )
            
            with col3:
                st.metric(
                    "❌ Failed",
                    self.failed,
                )
            
            with col4:
                st.metric(
                    "⏱️ ETA",
                    eta if total_processed < self.total_items else "Done",
                    f"{rate:.1f} items/s" if rate > 0 else ""
                )
            
            if self.current_item:
                st.caption(f"Current: {self.current_item}")
        
        # Update errors
        if self.errors:
            with self.error_container:
                for error in self.errors[-10:]:  # Show last 10 errors
                    st.error(error)
    
    def complete(self):
        """Mark batch operation as complete."""
        success_rate = (self.completed / self.total_items * 100) if self.total_items > 0 else 0
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if self.failed == 0:
            st.success(
                f"✅ {self.operation_name} completed successfully! "
                f"{self.completed}/{self.total_items} items processed "
                f"in {timedelta(seconds=int(elapsed))}"
            )
        else:
            st.warning(
                f"⚠️ {self.operation_name} completed with errors. "
                f"Success rate: {success_rate:.1f}% "
                f"({self.completed} succeeded, {self.failed} failed)"
            )

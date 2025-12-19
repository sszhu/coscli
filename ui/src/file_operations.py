"""File operation functions extracted from file_manager page."""

from typing import List, Dict
import streamlit as st

from ui.src.utils import get_cos_client
from ui.components.progress import BatchProgress


def filter_files(files: List[Dict], search_query: str = "", filter_type: str = "all") -> List[Dict]:
    """Apply search and filter to files.
    
    Args:
        files: List of file dictionaries
        search_query: Search string to filter by filename
        filter_type: File extension to filter by (e.g., '.csv', 'all')
    
    Returns:
        Filtered list of files
    """
    filtered = files
    
    if search_query:
        query = search_query.lower()
        filtered = [f for f in filtered if query in f['name'].lower()]
    
    if filter_type != 'all':
        filter_ext = filter_type.lower()
        filtered = [f for f in filtered if f['name'].lower().endswith(filter_ext)]
    
    return filtered


def sort_files(files: List[Dict], sort_by: str = 'name', sort_order: str = 'asc') -> List[Dict]:
    """Sort files by specified column and order.
    
    Args:
        files: List of file dictionaries
        sort_by: Column to sort by ('name', 'size', 'date')
        sort_order: Sort order ('asc' or 'desc')
    
    Returns:
        Sorted list of files
    """
    if sort_by == 'name':
        key_func = lambda f: f['name'].lower()
    elif sort_by == 'size':
        key_func = lambda f: f.get('size', 0)
    elif sort_by == 'date':
        key_func = lambda f: f.get('last_modified', '')
    else:
        key_func = lambda f: f['name'].lower()
    
    reverse = (sort_order == 'desc')
    return sorted(files, key=key_func, reverse=reverse)


def paginate_files(
    files: List[Dict],
    page_num: int = 1,
    page_size: int = 25
) -> tuple[List[Dict], int, int]:
    """Paginate files and return current page + total pages.
    
    Args:
        files: List of file dictionaries
        page_num: Current page number (1-indexed)
        page_size: Number of items per page
    
    Returns:
        Tuple of (page_files, page_num, total_pages)
    """
    total_pages = max(1, (len(files) + page_size - 1) // page_size)
    
    # Adjust page number if out of bounds
    if page_num > total_pages:
        page_num = total_pages
    
    start_idx = (page_num - 1) * page_size
    end_idx = start_idx + page_size
    
    return files[start_idx:end_idx], page_num, total_pages


def delete_files_batch(bucket: str, file_keys: List[str]) -> tuple[int, int]:
    """Delete multiple files with progress tracking.
    
    Args:
        bucket: Bucket name
        file_keys: List of file keys to delete
    
    Returns:
        Tuple of (success_count, failure_count)
    """
    cos_client = get_cos_client()
    if not cos_client:
        st.error("COS client not initialized")
        return 0, 0
    
    progress = BatchProgress(
        total_items=len(file_keys),
        operation_name="Deleting Files"
    )
    
    success_count = 0
    failure_count = 0
    
    for file_key in file_keys:
        progress.update_current(file_key)
        try:
            cos_client.delete_object(bucket=bucket, key=file_key)
            progress.mark_success(file_key)
            success_count += 1
        except Exception as e:
            progress.mark_failure(file_key, str(e))
            failure_count += 1
    
    progress.complete()
    return success_count, failure_count


def upload_files_batch(bucket: str, prefix: str, uploaded_files: List) -> tuple[int, int]:
    """Upload multiple files with progress tracking.
    
    Args:
        bucket: Bucket name
        prefix: Key prefix (folder path)
        uploaded_files: List of uploaded file objects
    
    Returns:
        Tuple of (success_count, failure_count)
    """
    cos_client = get_cos_client()
    if not cos_client:
        st.error("COS client not initialized")
        return 0, 0
    
    if not uploaded_files:
        return 0, 0
    
    if not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]
    
    progress = BatchProgress(
        total_items=len(uploaded_files),
        operation_name="Uploading Files"
    )
    
    success_count = 0
    failure_count = 0
    
    for uploaded_file in uploaded_files:
        progress.update_current(uploaded_file.name)
        
        try:
            key = prefix + uploaded_file.name
            cos_client.upload_file(
                bucket=bucket,
                key=key,
                file_obj=uploaded_file,
            )
            progress.mark_success(uploaded_file.name)
            success_count += 1
        except Exception as e:
            progress.mark_failure(uploaded_file.name, str(e))
            failure_count += 1
    
    progress.complete()
    return success_count, failure_count


def download_file(bucket: str, file: Dict) -> bytes:
    """Download a single file.
    
    Args:
        bucket: Bucket name
        file: File dictionary with 'key' and 'name'
    
    Returns:
        File content as bytes
    
    Raises:
        Exception: If download fails
    """
    cos_client = get_cos_client()
    if not cos_client:
        raise Exception("COS client not initialized")
    
    return cos_client.download_file(bucket=bucket, key=file['key'])


def get_presigned_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    """Generate presigned URL for file.
    
    Args:
        bucket: Bucket name
        key: File key
        expires_in: URL expiration time in seconds
    
    Returns:
        Presigned URL
    
    Raises:
        Exception: If generation fails
    """
    cos_client = get_cos_client()
    if not cos_client:
        raise Exception("COS client not initialized")
    
    return cos_client.get_presigned_url(
        bucket=bucket,
        key=key,
        expires_in=expires_in
    )


def create_folder(bucket: str, folder_path: str):
    """Create a folder (prefix) in COS.
    
    Args:
        bucket: Bucket name
        folder_path: Folder path to create
    
    Raises:
        Exception: If creation fails
    """
    cos_client = get_cos_client()
    if not cos_client:
        raise Exception("COS client not initialized")
    
    cos_client.create_folder(bucket=bucket, folder_path=folder_path)


def load_files_and_folders(bucket: str, prefix: str = "") -> tuple[List[Dict], List[str]]:
    """Load files and folders from COS.
    
    Args:
        bucket: Bucket name
        prefix: Key prefix to list under
    
    Returns:
        Tuple of (files, folders)
    """
    cos_client = get_cos_client()
    if not cos_client or not bucket:
        return [], []
    
    try:
        files, folders = cos_client.list_files_paginated(
            bucket=bucket,
            prefix=prefix,
            page_size=1000,
        )
        return files, folders
    except Exception as e:
        st.error(f"Failed to load files: {str(e)}")
        return [], []

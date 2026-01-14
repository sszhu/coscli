"""Utility functions for COS CLI"""

import json
import os
import time
import fnmatch
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from urllib.parse import urlparse
import threading

from rich.console import Console
from rich.table import Table
from tabulate import tabulate

from .constants import COS_URI_SCHEME
from .exceptions import InvalidURIError

console = Console()


def parse_cos_uri(uri: str) -> tuple[str, str]:
    """
    Parse COS URI into bucket and key.
    
    Args:
        uri: COS URI in format cos://bucket/key
        
    Returns:
        Tuple of (bucket, key)
        
    Raises:
        InvalidURIError: If URI is invalid
    """
    if not uri.startswith(COS_URI_SCHEME):
        raise InvalidURIError(f"URI must start with {COS_URI_SCHEME}")
    
    # Remove scheme
    path = uri[len(COS_URI_SCHEME):]
    
    # Split into bucket and key
    parts = path.split("/", 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ""
    
    if not bucket:
        raise InvalidURIError("Bucket name cannot be empty")
    
    return bucket, key


def parse_size_to_bytes(size: Optional[str | int | float]) -> int:
    """Parse a human-friendly size string into bytes.

    Accepts integers (already bytes) or strings like '8MB', '64kb', '1g'.
    Defaults to 8MB when input is None.
    """
    default = 8 * 1024 * 1024
    if size is None:
        return default
    if isinstance(size, (int, float)):
        return int(size)
    s = str(size).strip().lower()
    if not s:
        return default
    units = {
        'b': 1,
        'kb': 1024,
        'k': 1024,
        'mb': 1024 * 1024,
        'm': 1024 * 1024,
        'gb': 1024 * 1024 * 1024,
        'g': 1024 * 1024 * 1024,
    }
    # Extract numeric and unit
    num = ''
    unit = ''
    for ch in s:
        if ch.isdigit() or ch == '.' or (ch == '-' and not num):
            num += ch
        else:
            unit += ch
    try:
        val = float(num) if num else 0
    except ValueError:
        return default
    unit = unit.strip() or 'b'
    mult = units.get(unit, 1)
    return int(val * mult)


def validate_bucket_name(bucket: str) -> bool:
    """
    Validate Tencent COS bucket name.
    
    Bucket naming rules:
    - Length: 1-50 characters
    - Can contain lowercase letters, numbers, and hyphens
    - Must start and end with lowercase letter or number
    - Cannot contain consecutive hyphens
    
    Args:
        bucket: Bucket name to validate
        
    Returns:
        True if valid, False otherwise
    """
    import re
    
    if not bucket or len(bucket) < 1 or len(bucket) > 50:
        return False
    
    # Check pattern: lowercase alphanumeric and hyphens
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', bucket):
        return False
    
    # Check for consecutive hyphens
    if '--' in bucket:
        return False
    
    return True


def format_size(size) -> str:
    """
    Format size in bytes to human-readable format.
    
    Args:
        size: Size in bytes (int or str)
        
    Returns:
        Human-readable size string
    """
    # Convert to int if string
    try:
        size = int(size)
    except (ValueError, TypeError):
        return "0.0 B"
    
    size = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_datetime(dt) -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime object or ISO format string
        
    Returns:
        Formatted datetime string
    """
    if not dt:
        return "N/A"
    
    # Parse string to datetime if needed
    if isinstance(dt, str):
        try:
            # Try ISO format first (common from COS API)
            dt_parsed = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            return dt_parsed.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            try:
                # Try common datetime formats
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                    try:
                        dt_parsed = datetime.strptime(dt, fmt)
                        return dt_parsed.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue
                # Return original string if parsing fails
                return dt
            except Exception:
                return dt
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def output_table(data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> None:
    """
    Output data as a table.
    
    Args:
        data: List of dictionaries containing data
        headers: Optional list of headers (uses dict keys if not provided)
    """
    if not data:
        return
    
    if headers is None:
        headers = list(data[0].keys())
    
    table = Table(show_header=True, header_style="bold magenta")
    
    for header in headers:
        table.add_column(header)
    
    for row in data:
        table.add_row(*[str(row.get(h, "")) for h in headers])
    
    console.print(table)


def output_json(data: Any) -> None:
    """
    Output data as JSON.
    
    Args:
        data: Data to output
    """
    print(json.dumps(data, indent=2, default=str))


def output_text(data: List[str]) -> None:
    """
    Output data as plain text.
    
    Args:
        data: List of strings to output
    """
    for item in data:
        print(item)


def format_output(data: Any, output_format: str = "table") -> None:
    """
    Format and output data based on format type.
    
    Args:
        data: Data to output
        output_format: Output format (json, table, text)
    """
    if output_format == "json":
        output_json(data)
    elif output_format == "text":
        if isinstance(data, list):
            output_text(data)
        else:
            output_text([str(data)])
    else:  # table
        if isinstance(data, list) and data and isinstance(data[0], dict):
            output_table(data)
        else:
            print(data)


def ensure_directory(path: Path) -> None:
    """
    Ensure directory exists, create if not.
    
    Args:
        path: Path to directory
    """
    path.mkdir(parents=True, exist_ok=True)


def get_file_md5(filepath: str, chunk_size: int = 8192) -> str:
    """
    Calculate MD5 hash of a file.
    
    Args:
        filepath: Path to file
        chunk_size: Size of chunks to read
        
    Returns:
        MD5 hash as hex string
    """
    import hashlib
    
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
    return md5.hexdigest()


def is_cos_uri(path: str) -> bool:
    """
    Check if path is a COS URI.
    
    Args:
        path: Path to check
        
    Returns:
        True if path is COS URI
    """
    return path.startswith(COS_URI_SCHEME)


def join_cos_path(*parts: str) -> str:
    """
    Join COS path parts.
    
    Args:
        parts: Path parts to join
        
    Returns:
        Joined path
    """
    return "/".join(p.strip("/") for p in parts if p)


def error_message(message: str, exception: Optional[Exception] = None) -> None:
    """
    Display error message.
    
    Args:
        message: Error message
        exception: Optional exception to display
    """
    console.print(f"[bold red]Error:[/bold red] {message}")
    if exception:
        console.print(f"[dim]{str(exception)}[/dim]")


def success_message(message: str) -> None:
    """
    Display success message.
    
    Args:
        message: Success message
    """
    console.print(f"[bold green]✓[/bold green] {message}")


def info_message(message: str) -> None:
    """
    Display info message.
    
    Args:
        message: Info message
    """
    console.print(f"[bold blue]ℹ[/bold blue] {message}")

def matches_pattern(path: str, patterns: List[str], is_include: bool = True) -> bool:
    """
    Check if path matches any of the given patterns.
    
    Args:
        path: File path to check
        patterns: List of glob patterns
        is_include: True for include patterns, False for exclude
        
    Returns:
        True if path matches (for include) or doesn't match (for exclude)
    """
    if not patterns:
        return True if is_include else False
    
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def should_process_file(
    path: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> bool:
    """
    Determine if a file should be processed based on include/exclude patterns.
    
    Args:
        path: File path to check
        include_patterns: List of include patterns (if specified, only matching files are included)
        exclude_patterns: List of exclude patterns (matching files are excluded)
        
    Returns:
        True if file should be processed
    """
    # If include patterns specified, file must match at least one
    if include_patterns and not matches_pattern(path, include_patterns, True):
        return False
    
    # If exclude patterns specified, file must not match any
    if exclude_patterns and matches_pattern(path, exclude_patterns, True):
        return False
    
    return True


class BandwidthThrottle:
    """Throttle bandwidth for uploads/downloads"""
    
    def __init__(self, max_bytes_per_sec: Optional[int] = None):
        """
        Initialize bandwidth throttle.
        
        Args:
            max_bytes_per_sec: Maximum bytes per second (None = no limit)
        """
        self.max_bytes_per_sec = max_bytes_per_sec
        self.bytes_transferred = 0
        self.start_time = time.time()
        self._lock = threading.Lock()
    
    def throttle(self, chunk_size: int) -> None:
        """
        Apply throttle based on bytes transferred.
        
        Args:
            chunk_size: Size of chunk being transferred
        """
        if self.max_bytes_per_sec is None:
            return
        
        with self._lock:
            self.bytes_transferred += chunk_size
            elapsed = time.time() - self.start_time
            expected_time = self.bytes_transferred / self.max_bytes_per_sec
            
            if expected_time > elapsed:
                time.sleep(expected_time - elapsed)
    
    def get_speed(self) -> float:
        """
        Get current transfer speed in bytes per second.
        
        Returns:
            Transfer speed
        """
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return 0
        return self.bytes_transferred / elapsed


class ResumeTracker:
    """Track transfer progress for resume capability"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize resume tracker.
        
        Args:
            cache_dir: Directory to store progress cache (default: ~/.cos/cache)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cos" / "cache"
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_file(self, file_path: str, operation: str) -> Path:
        """Get cache file path for a transfer"""
        file_hash = hashlib.md5(f"{file_path}{operation}".encode()).hexdigest()
        return self.cache_dir / f"{file_hash}.json"
    
    def save_progress(self, file_path: str, operation: str, data: Dict) -> None:
        """
        Save progress for a transfer.
        
        Args:
            file_path: File being transferred
            operation: Operation type (upload/download)
            data: Progress data to save
        """
        cache_file = self.get_cache_file(file_path, operation)
        with open(cache_file, 'w') as f:
            json.dump({
                'file_path': file_path,
                'operation': operation,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }, f)
    
    def load_progress(self, file_path: str, operation: str) -> Optional[Dict]:
        """
        Load progress for a transfer.
        
        Args:
            file_path: File being transferred
            operation: Operation type (upload/download)
            
        Returns:
            Progress data or None if not found
        """
        cache_file = self.get_cache_file(file_path, operation)
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def clear_progress(self, file_path: str, operation: str) -> None:
        """
        Clear progress for a completed transfer.
        
        Args:
            file_path: File being transferred
            operation: Operation type (upload/download)
        """
        cache_file = self.get_cache_file(file_path, operation)
        if cache_file.exists():
            cache_file.unlink()


def compute_file_checksum(file_path: str, algorithm: str = "md5") -> str:
    """
    Compute checksum of a file.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256)
        
    Returns:
        Hex digest of checksum
    """
    if algorithm == "md5":
        hasher = hashlib.md5()
    elif algorithm == "sha1":
        hasher = hashlib.sha1()
    elif algorithm == "sha256":
        hasher = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def compare_checksums(local_path: str, remote_etag: str) -> bool:
    """
    Compare local file checksum with remote ETag.
    
    Args:
        local_path: Path to local file
        remote_etag: ETag from COS (typically MD5)
        
    Returns:
        True if checksums match
    """
    # Remove quotes from ETag if present
    remote_etag = remote_etag.strip('"')
    
    # For multipart uploads, ETag is not a simple MD5
    # If ETag contains '-', it's a multipart upload
    if '-' in remote_etag:
        # Can't reliably compare multipart ETags
        return False
    
    local_md5 = compute_file_checksum(local_path, "md5")
    return local_md5 == remote_etag
"""Utility functions for COS CLI"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

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

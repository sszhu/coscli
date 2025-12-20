"""Copy command for COS CLI"""

import os
from pathlib import Path

import click
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from ..auth import COSAuthenticator
from ..client import COSClient
from ..config import ConfigManager
from ..utils import (
    parse_cos_uri,
    is_cos_uri,
    success_message,
    error_message,
    should_process_file,
)
from ..exceptions import COSError


@click.command()
@click.argument("source")
@click.argument("destination")
@click.option("--recursive", "-r", is_flag=True, help="Copy directories recursively")
@click.option("--include", multiple=True, help="Include files matching pattern")
@click.option("--exclude", multiple=True, help="Exclude files matching pattern")
@click.option("--no-progress", is_flag=True, help="Disable progress bar")
@click.pass_context
def cp(ctx, source, destination, recursive, include, exclude, no_progress):
    """
    Copy files to/from COS.

    \b
    Examples:
      cos cp file.txt cos://bucket/file.txt       # Upload
      cos cp cos://bucket/file.txt ./local.txt    # Download
      cos cp cos://b1/f cos://b2/f                # Copy between buckets
      cos cp ./dir/ cos://bucket/dir/ -r          # Upload directory
    """
    try:
        # Get config and auth
        profile = ctx.obj.get("profile", "default")
        region = ctx.obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        
        source_is_cos = is_cos_uri(source)
        dest_is_cos = is_cos_uri(destination)
        
        # Determine operation type
        if source_is_cos and not dest_is_cos:
            # Download
            _download_files(ctx, cos_client_raw, source, destination, recursive, include, exclude, no_progress)
        elif not source_is_cos and dest_is_cos:
            # Upload
            _upload_files(ctx, cos_client_raw, source, destination, recursive, include, exclude, no_progress)
        elif source_is_cos and dest_is_cos:
            # Copy between buckets
            _copy_objects(ctx, cos_client_raw, source, destination, recursive, include, exclude, no_progress)
        else:
            raise COSError("At least one path must be a COS URI (cos://...)")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        if ctx.obj.get("debug"):
            raise
        error_message("An unexpected error occurred", e)
        ctx.exit(1)


def _upload_files(ctx, cos_client_raw, source, destination, recursive, include, exclude, no_progress):
    """Upload local files to COS"""
    bucket, key = parse_cos_uri(destination)
    cos_client = COSClient(cos_client_raw, bucket)
    
    source_path = Path(source)
    
    if source_path.is_file():
        # Single file upload - check patterns
        if not should_process_file(source_path.name, list(include) if include else None, list(exclude) if exclude else None):
            error_message(f"Skipping {source} (excluded by pattern)")
            return
        
        # If destination ends with /, append source filename
        if key and key.endswith('/'):
            target_key = key + source_path.name
        else:
            target_key = key or source_path.name
        
        if not no_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                TransferSpeedColumn(),
            ) as progress:
                task = progress.add_task(f"Uploading {source_path.name}...", total=source_path.stat().st_size)
                cos_client.upload_file(str(source_path), target_key)
                progress.update(task, completed=source_path.stat().st_size)
        else:
            cos_client.upload_file(str(source_path), target_key)
        
        success_message(f"Uploaded {source} to cos://{bucket}/{target_key}")
    
    elif source_path.is_dir():
        if not recursive:
            raise COSError("Use --recursive to upload directories")
        
        # Directory upload - apply patterns
        files = list(source_path.rglob("*"))
        files = [f for f in files if f.is_file()]
        
        # Filter by patterns
        include_patterns = list(include) if include else None
        exclude_patterns = list(exclude) if exclude else None
        filtered_files = [
            f for f in files
            if should_process_file(f.name, include_patterns, exclude_patterns)
        ]
        
        if not filtered_files:
            error_message("No files match the specified patterns")
            return
        
        if not no_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
            ) as progress:
                task = progress.add_task(f"Uploading {len(filtered_files)} files...", total=len(filtered_files))
                
                for file_path in filtered_files:
                    rel_path = file_path.relative_to(source_path)
                    dest_key = f"{key}/{rel_path}".strip("/") if key else str(rel_path)
                    cos_client.upload_file(str(file_path), dest_key)
                    progress.update(task, advance=1)
        else:
            for file_path in filtered_files:
                rel_path = file_path.relative_to(source_path)
                dest_key = f"{key}/{rel_path}".strip("/") if key else str(rel_path)
                cos_client.upload_file(str(file_path), dest_key)
        
        success_message(f"Uploaded {len(filtered_files)} files to cos://{bucket}/{key}")
    else:
        raise COSError(f"Source path does not exist: {source}")


def _download_files(ctx, cos_client_raw, source, destination, recursive, include, exclude, no_progress):
    """Download files from COS to local"""
    bucket, key = parse_cos_uri(source)
    cos_client = COSClient(cos_client_raw, bucket)
    
    dest_path = Path(destination)
    
    if not recursive:
        # Single file download - check patterns
        filename = key.split('/')[-1] if '/' in key else key
        if not should_process_file(filename, list(include) if include else None, list(exclude) if exclude else None):
            error_message(f"Skipping {key} (excluded by pattern)")
            return
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not no_progress:
            # Get file size first
            try:
                head_response = cos_client.head_object(key)
                file_size = int(head_response.get("Content-Length", 0))
            except:
                file_size = None
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                TransferSpeedColumn(),
            ) as progress:
                task = progress.add_task(f"Downloading {key}...", total=file_size)
                cos_client.download_file(key, str(dest_path))
                if file_size:
                    progress.update(task, completed=file_size)
        else:
            cos_client.download_file(key, str(dest_path))
        
        success_message(f"Downloaded cos://{bucket}/{key} to {destination}")
    else:
        # Directory download - apply patterns
        response = cos_client.list_objects(prefix=key, delimiter="")
        objects = response.get("Contents", [])
        
        # Filter by patterns
        include_patterns = list(include) if include else None
        exclude_patterns = list(exclude) if exclude else None
        filtered_objects = [
            obj for obj in objects
            if should_process_file(obj.get("Key", "").split('/')[-1], include_patterns, exclude_patterns)
        ]
        
        if not filtered_objects:
            error_message("No files match the specified patterns")
            return
        
        if not no_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
            ) as progress:
                task = progress.add_task(f"Downloading {len(filtered_objects)} files...", total=len(filtered_objects))
                
                for obj in filtered_objects:
                    obj_key = obj.get("Key", "")
                    rel_path = obj_key[len(key):].lstrip("/")
                    local_path = dest_path / rel_path
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    cos_client.download_file(obj_key, str(local_path))
                    progress.update(task, advance=1)
        else:
            for obj in filtered_objects:
                obj_key = obj.get("Key", "")
                rel_path = obj_key[len(key):].lstrip("/")
                local_path = dest_path / rel_path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                cos_client.download_file(obj_key, str(local_path))
        
        success_message(f"Downloaded {len(filtered_objects)} files to {destination}")


def _copy_objects(ctx, cos_client_raw, source, destination, recursive, include, exclude, no_progress):
    """Copy objects between COS locations"""
    source_bucket, source_key = parse_cos_uri(source)
    dest_bucket, dest_key = parse_cos_uri(destination)
    
    cos_client = COSClient(cos_client_raw)
    
    if not recursive:
        # Single object copy - check patterns
        filename = source_key.split('/')[-1] if '/' in source_key else source_key
        if not should_process_file(filename, list(include) if include else None, list(exclude) if exclude else None):
            error_message(f"Skipping {source_key} (excluded by pattern)")
            return
        
        cos_client.copy_object(source_bucket, source_key, dest_bucket, dest_key)
        success_message(f"Copied cos://{source_bucket}/{source_key} to cos://{dest_bucket}/{dest_key}")
    else:
        # Multiple objects copy - apply patterns
        source_cos = COSClient(cos_client_raw, source_bucket)
        response = source_cos.list_objects(prefix=source_key, delimiter="")
        objects = response.get("Contents", [])
        
        # Filter by patterns
        include_patterns = list(include) if include else None
        exclude_patterns = list(exclude) if exclude else None
        filtered_objects = [
            obj for obj in objects
            if should_process_file(obj.get("Key", "").split('/')[-1], include_patterns, exclude_patterns)
        ]
        
        if not filtered_objects:
            error_message("No files match the specified patterns")
            return
        
        if not no_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
            ) as progress:
                task = progress.add_task(f"Copying {len(filtered_objects)} objects...", total=len(filtered_objects))
                
                for obj in filtered_objects:
                    obj_key = obj.get("Key", "")
                    rel_path = obj_key[len(source_key):].lstrip("/")
                    new_dest_key = f"{dest_key}/{rel_path}".strip("/") if dest_key else rel_path
                    cos_client.copy_object(source_bucket, obj_key, dest_bucket, new_dest_key)
                    progress.update(task, advance=1)
        else:
            for obj in filtered_objects:
                obj_key = obj.get("Key", "")
                rel_path = obj_key[len(source_key):].lstrip("/")
                new_dest_key = f"{dest_key}/{rel_path}".strip("/") if dest_key else rel_path
                cos_client.copy_object(source_bucket, obj_key, dest_bucket, new_dest_key)
        
        success_message(f"Copied {len(filtered_objects)} objects to cos://{dest_bucket}/{dest_key}")

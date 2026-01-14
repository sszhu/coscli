"""Sync command for COS CLI - Synchronize directories"""

import click
import os
from pathlib import Path
from datetime import datetime

from ..auth import COSAuthenticator
from ..client import COSClient
from ..config import ConfigManager
from ..utils import (
    parse_cos_uri,
    is_cos_uri,
    success_message,
    error_message,
    info_message,
    format_size,
    should_process_file,
    compare_checksums,
)
from ..exceptions import COSError


def get_local_files(directory):
    """Get list of local files with metadata"""
    files = {}
    base_path = Path(directory).resolve()
    
    for file_path in base_path.rglob("*"):
        if file_path.is_file():
            relative_path = str(file_path.relative_to(base_path))
            stat = file_path.stat()
            files[relative_path] = {
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "path": str(file_path)
            }
    
    return files


def get_cos_files(cos_client, prefix=""):
    """Get list of COS objects with metadata"""
    files = {}
    response = cos_client.list_objects(prefix=prefix, delimiter="")
    
    # Extract objects from response dictionary
    objects = response.get("Contents", [])
    
    for obj in objects:
        key = obj["Key"]
        # Remove prefix to get relative path
        relative_key = key[len(prefix):].lstrip("/") if prefix else key
        
        last_modified = obj.get("LastModified")
        if last_modified:
            mtime = datetime.fromisoformat(last_modified.replace('Z', '+00:00')).timestamp()
        else:
            mtime = 0.0
        files[relative_key] = {
            "size": obj.get("Size", 0),
            "mtime": mtime,
            "key": key,
            "etag": obj.get("ETag", "").strip('"')
        }
    
    return files


@click.command()
@click.argument("source")
@click.argument("destination")
@click.option("--delete", is_flag=True, help="Delete files in destination not in source")
@click.option("--dryrun", "-n", is_flag=True, help="Show what would be done without doing it")
@click.option("--size-only", is_flag=True, help="Skip files with same size (faster)")
@click.option("--checksum", is_flag=True, help="Use checksums for comparison (slower but accurate)")
@click.option("--include", multiple=True, help="Include files matching pattern")
@click.option("--exclude", multiple=True, help="Exclude files matching pattern")
@click.option("--no-progress", is_flag=True, help="Disable progress bar")
@click.pass_context
@click.option("--part-size", type=str, default=None, help="Part size for multipart/ranged transfers (e.g., 8MB, 64MB)")
@click.option("--max-retries", type=int, default=3, help="Max retries for part/range operations")
@click.option("--retry-backoff", type=float, default=0.5, help="Initial backoff seconds between retries")
@click.option("--retry-backoff-max", type=float, default=5.0, help="Max backoff seconds for retries")
@click.option("--resume/--no-resume", default=True, help="Resume interrupted ranged downloads")
def sync(ctx, source, destination, delete, dryrun, size_only, checksum, include, exclude, no_progress, part_size, max_retries, retry_backoff, retry_backoff_max, resume):
    """
    Synchronize directories between local and COS.

    \b
    Examples:
      cos sync ./local/ cos://bucket/path/          # Upload local to COS
      cos sync cos://bucket/path/ ./local/          # Download COS to local
      cos sync ./local/ cos://bucket/ --delete      # Sync and delete extras
      cos sync ./local/ cos://bucket/ --dryrun      # Preview changes
      cos sync ./local/ cos://bucket/ --checksum    # Use MD5 checksums
      cos sync ./local/ cos://bucket/ --include "*.txt"  # Only .txt files
    """
    try:
        # Determine sync direction
        src_is_cos = is_cos_uri(source)
        dst_is_cos = is_cos_uri(destination)
        
        if src_is_cos and dst_is_cos:
            error_message("COS to COS sync not yet supported")
            ctx.exit(1)
        
        if not src_is_cos and not dst_is_cos:
            error_message("Both source and destination are local paths. Use rsync instead.")
            ctx.exit(1)
        
        # Get config and auth
        ctx_obj = ctx.obj or {}
        profile = ctx_obj.get("profile", "default")
        region = ctx_obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        
        if dryrun:
            info_message("DRY RUN MODE - No changes will be made")
            click.echo()
        
        # Local to COS sync
        if not src_is_cos and dst_is_cos:
            bucket, prefix = parse_cos_uri(destination)
            cos_client = COSClient(cos_client_raw, bucket)
            
            # Get file lists
            local_files = get_local_files(source)
            cos_files = get_cos_files(cos_client, prefix)
            
            # Apply patterns
            include_patterns = list(include) if include else None
            exclude_patterns = list(exclude) if exclude else None
            if include_patterns or exclude_patterns:
                local_files = {
                    k: v for k, v in local_files.items()
                    if should_process_file(k, include_patterns, exclude_patterns)
                }
            
            upload_count = 0
            delete_count = 0
            skip_count = 0
            
            # Upload new/modified files
            for rel_path, local_info in local_files.items():
                cos_key = (prefix.rstrip("/") + "/" + rel_path) if prefix else rel_path
                
                needs_upload = False
                
                if rel_path not in cos_files:
                    needs_upload = True
                    info_message(f"NEW: {rel_path}")
                elif checksum:
                    # Use MD5 checksum comparison
                    cos_etag = cos_files[rel_path].get("etag", "")
                    if not compare_checksums(local_info["path"], cos_etag):
                        needs_upload = True
                        info_message(f"CHECKSUM DIFF: {rel_path}")
                elif size_only:
                    if local_info["size"] != cos_files[rel_path]["size"]:
                        needs_upload = True
                        info_message(f"SIZE DIFF: {rel_path}")
                else:
                    if (local_info["size"] != cos_files[rel_path]["size"] or 
                        local_info["mtime"] > cos_files[rel_path]["mtime"]):
                        needs_upload = True
                        info_message(f"MODIFIED: {rel_path}")
                
                if needs_upload:
                    if not dryrun:
                        if no_progress:
                            cos_client.upload_file(local_info["path"], cos_key)
                        else:
                            # Multipart with progress and retries
                            from rich.progress import (
                                Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TransferSpeedColumn, TimeRemainingColumn
                            )
                            from ..transfer import upload_file_multipart_with_progress
                            from ..utils import parse_size_to_bytes
                            ps = parse_size_to_bytes(part_size)
                            file_size = local_info["size"]
                            with Progress(
                                SpinnerColumn(),
                                TextColumn("[progress.description]{task.description}"),
                                BarColumn(),
                                TaskProgressColumn(),
                                TransferSpeedColumn(),
                                TimeRemainingColumn(),
                            ) as progress:
                                task = progress.add_task(f"Uploading {rel_path}...", total=file_size)
                                def on_update(done, _total):
                                    progress.update(task, completed=done)
                                upload_file_multipart_with_progress(
                                    cos_client_raw,
                                    bucket,
                                    cos_key,
                                    Path(local_info["path"]),
                                    chunk_size=ps,
                                    progress_update=on_update,
                                    max_retries=max_retries,
                                    retry_backoff=retry_backoff,
                                    retry_backoff_max=retry_backoff_max,
                                )
                    upload_count += 1
                else:
                    skip_count += 1
            
            # Delete files not in source
            if delete:
                for rel_path, cos_info in cos_files.items():
                    if rel_path not in local_files:
                        info_message(f"DELETE: {rel_path}")
                        if not dryrun:
                            cos_client.delete_object(cos_info["key"])
                        delete_count += 1
            
            # Summary
            click.echo()
            if dryrun:
                info_message("DRY RUN SUMMARY:")
            else:
                success_message("SYNC COMPLETE:")
            
            click.echo(f"  Uploaded: {upload_count}")
            click.echo(f"  Skipped:  {skip_count}")
            if delete:
                click.echo(f"  Deleted:  {delete_count}")
        
        # COS to Local sync
        else:
            bucket, prefix = parse_cos_uri(source)
            cos_client = COSClient(cos_client_raw, bucket)
            
            # Get file lists
            cos_files = get_cos_files(cos_client, prefix)
            local_files = get_local_files(destination)
            
            # Apply patterns
            include_patterns = list(include) if include else None
            exclude_patterns = list(exclude) if exclude else None
            if include_patterns or exclude_patterns:
                cos_files = {
                    k: v for k, v in cos_files.items()
                    if should_process_file(k, include_patterns, exclude_patterns)
                }
            
            download_count = 0
            delete_count = 0
            skip_count = 0
            
            # Download new/modified files
            for rel_path, cos_info in cos_files.items():
                local_path = Path(destination) / rel_path
                
                needs_download = False
                
                if rel_path not in local_files:
                    needs_download = True
                    info_message(f"NEW: {rel_path}")
                elif checksum:
                    # Use MD5 checksum comparison
                    if local_path.exists():
                        if not compare_checksums(str(local_path), cos_info.get("etag", "")):
                            needs_download = True
                            info_message(f"CHECKSUM DIFF: {rel_path}")
                    else:
                        needs_download = True
                elif size_only:
                    if cos_info["size"] != local_files[rel_path]["size"]:
                        needs_download = True
                        info_message(f"SIZE DIFF: {rel_path}")
                else:
                    if (cos_info["size"] != local_files[rel_path]["size"] or
                        cos_info["mtime"] > local_files[rel_path]["mtime"]):
                        needs_download = True
                        info_message(f"MODIFIED: {rel_path}")
                
                if needs_download:
                    if not dryrun:
                        local_path.parent.mkdir(parents=True, exist_ok=True)
                        if no_progress:
                            cos_client.download_file(cos_info["key"], str(local_path))
                        else:
                            # Use ranged download with retries and optional resume
                            from ..transfer import download_file_in_ranges_with_progress
                            from ..utils import parse_size_to_bytes, ResumeTracker
                            ps = parse_size_to_bytes(part_size)
                            total_size = int(cos_info.get("size", 0))
                            tracker = ResumeTracker() if resume else None
                            # Minimal per-file progress in sync mode (could be aggregated later)
                            def noop(done, total):
                                return None
                            download_file_in_ranges_with_progress(
                                cos_client_raw,
                                bucket,
                                cos_info["key"],
                                local_path,
                                total_size=total_size,
                                chunk_size=ps,
                                progress_update=noop,
                                resume=resume,
                                resume_tracker=tracker,
                                max_retries=max_retries,
                                retry_backoff=retry_backoff,
                                retry_backoff_max=retry_backoff_max,
                            )
                    download_count += 1
                else:
                    skip_count += 1
            
            # Delete local files not in COS
            if delete:
                for rel_path, local_info in local_files.items():
                    if rel_path not in cos_files:
                        info_message(f"DELETE: {rel_path}")
                        if not dryrun:
                            Path(local_info["path"]).unlink()
                        delete_count += 1
            
            # Summary
            click.echo()
            if dryrun:
                info_message("DRY RUN SUMMARY:")
            else:
                success_message("SYNC COMPLETE:")
            
            click.echo(f"  Downloaded: {download_count}")
            click.echo(f"  Skipped:    {skip_count}")
            if delete:
                click.echo(f"  Deleted:    {delete_count}")
            
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)
    except Exception as e:
        error_message(f"Failed to sync: {e}")
        if ctx.obj.get("debug"):
            raise
        ctx.exit(1)

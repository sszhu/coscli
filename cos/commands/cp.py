"""Copy command for COS CLI"""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from ..transfer import (
    download_file_with_progress_polling,
    upload_file_multipart_with_progress,
    download_file_in_ranges_with_progress,
)
from ..utils import (
    parse_cos_uri,
    is_cos_uri,
    success_message,
    error_message,
    should_process_file,
)
from ..exceptions import COSError, ObjectNotFoundError


@click.command()
@click.argument("source")
@click.argument("destination")
@click.option("--recursive", "-r", is_flag=True, help="Copy directories recursively")
@click.option("--include", multiple=True, help="Include files matching pattern")
@click.option("--exclude", multiple=True, help="Exclude files matching pattern")
@click.option("--no-progress", is_flag=True, help="Disable progress bar")
@click.option("--concurrency", "concurrency", type=int, default=4, help="Number of parallel transfers for bulk operations")
@click.option("--part-size", type=str, default=None, help="Part size for multipart and ranged transfers (e.g., 8MB, 64MB)")
@click.option("--max-retries", type=int, default=3, help="Max retries for part/range operations")
@click.option("--retry-backoff", type=float, default=0.5, help="Initial backoff seconds between retries")
@click.option("--retry-backoff-max", type=float, default=5.0, help="Max backoff seconds for retries")
@click.option("--resume/--no-resume", default=True, help="Resume interrupted ranged downloads")
@click.pass_context
def cp(ctx, source, destination, recursive, include, exclude, no_progress, concurrency, part_size, max_retries, retry_backoff, retry_backoff_max, resume):
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
        ctx_obj = ctx.obj or {}
        profile = ctx_obj.get("profile", "default")
        region = ctx_obj.get("region")
        
        config_manager = ConfigManager(profile)
        authenticator = COSAuthenticator(config_manager)
        cos_client_raw = authenticator.authenticate(region)
        
        source_is_cos = is_cos_uri(source)
        dest_is_cos = is_cos_uri(destination)
        
        # Detect non-TTY and disable progress unless explicitly enabled
        auto_no_progress = not sys.stdout.isatty()
        if auto_no_progress:
            no_progress = True

        # Determine operation type
        if source_is_cos and not dest_is_cos:
            # Download
            _download_files(
                ctx, cos_client_raw, source, destination, recursive, include, exclude, no_progress, concurrency,
                part_size, max_retries, retry_backoff, retry_backoff_max, resume
            )
        elif not source_is_cos and dest_is_cos:
            # Upload
            _upload_files(
                ctx, cos_client_raw, source, destination, recursive, include, exclude, no_progress, concurrency,
                part_size, max_retries, retry_backoff, retry_backoff_max
            )
        elif source_is_cos and dest_is_cos:
            # Copy between buckets
            _copy_objects(ctx, cos_client_raw, source, destination, recursive, include, exclude, no_progress)
        else:
            raise COSError("At least one path must be a COS URI (cos://...)")
    
    except COSError as e:
        error_message(str(e))
        ctx.exit(1)


def _upload_files(_ctx, cos_client_raw, source, destination, recursive, include, exclude, no_progress, concurrency, part_size, max_retries, retry_backoff, retry_backoff_max):
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
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                file_size = source_path.stat().st_size
                task = progress.add_task(
                    f"Uploading {source_path.name}...", total=file_size
                )
                # Use multipart upload for streaming progress
                def on_update(done, _total):
                    progress.update(task, completed=done)
                # resolve part size
                from ..utils import parse_size_to_bytes
                ps = parse_size_to_bytes(part_size)
                upload_file_multipart_with_progress(
                    cos_client_raw,
                    bucket,
                    target_key,
                    source_path,
                    chunk_size=ps,
                    progress_update=on_update,
                    max_retries=max_retries,
                    retry_backoff=retry_backoff,
                    retry_backoff_max=retry_backoff_max,
                )
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
        
        # Aggregate total bytes for progress
        file_sizes = {f: f.stat().st_size for f in filtered_files}
        total_bytes = sum(file_sizes.values())

        if not no_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(f"Uploading {len(filtered_files)} files...", total=total_bytes)

                def do_upload(file_path: Path):
                    rel_path = file_path.relative_to(source_path)
                    dest_key = (f"{key.rstrip('/')}/{rel_path}").lstrip("/") if key else str(rel_path)
                    cos_client.upload_file(str(file_path), dest_key)
                    progress.update(task, advance=file_sizes[file_path])

                with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
                    futures = [executor.submit(do_upload, fp) for fp in filtered_files]
                    for fut in as_completed(futures):
                        exc = fut.exception()
                        if exc:
                            raise exc
        else:
            with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
                def do_upload(file_path: Path):
                    rel_path = file_path.relative_to(source_path)
                    dest_key = (f"{key.rstrip('/')}/{rel_path}").lstrip("/") if key else str(rel_path)
                    cos_client.upload_file(str(file_path), dest_key)
                futures = [executor.submit(do_upload, fp) for fp in filtered_files]
                for fut in as_completed(futures):
                    exc = fut.exception()
                    if exc:
                        raise exc
        
        success_message(f"Uploaded {len(filtered_files)} files to cos://{bucket}/{key}")
    else:
        raise COSError(f"Source path does not exist: {source}")


def _download_files(_ctx, cos_client_raw, source, destination, recursive, include, exclude, no_progress, concurrency, part_size, max_retries, retry_backoff, retry_backoff_max, resume):
    """Download files from COS to local"""
    bucket, key = parse_cos_uri(source)
    cos_client = COSClient(cos_client_raw, bucket)
    
    dest_path = Path(destination)
    
    def _resolve_remote_size() -> int:
        """Resolve object size reliably using HEAD, then list, then ranged GET.

        Returns 0 if size cannot be determined.
        Raises ObjectNotFoundError if the object does not exist.
        """
        # Try HEAD first
        try:
            head_response = cos_client.head_object(key)
            # Different SDKs/versions may use different keys
            if hasattr(head_response, "get"):
                for k in ("Content-Length", "ContentLength", "content-length"):
                    try:
                        v = head_response.get(k)
                        if v is None:
                            continue
                        size_val = int(v)
                        if size_val > 0:
                            return size_val
                    except (TypeError, ValueError):
                        continue
        except ObjectNotFoundError:
            # Bubble up for caller to handle
            raise
        except COSError:
            # Fall through to other strategies
            pass

        # Fallback to ListObjects to locate exact key size
        try:
            listing = cos_client.list_objects(prefix=key, delimiter="")
            for obj in listing.get("Contents", []):
                if obj.get("Key") == key:
                    try:
                        size_val = int(obj.get("Size", 0))
                        if size_val > 0:
                            return size_val
                    except (TypeError, ValueError):
                        pass
        except COSError:
            pass

        # Final fallback: ranged GET 0-0 and parse Content-Range header
        try:
            resp = cos_client_raw.get_object(Bucket=bucket, Key=key, Range="bytes=0-0")
            # SDK may provide headers directly or within response metadata
            cr = (
                resp.get("Content-Range")
                or getattr(resp, "headers", {}).get("Content-Range")
                or resp.get("ResponseHeaders", {}).get("Content-Range")
            )
            if isinstance(cr, str) and "/" in cr:
                total_part = cr.split("/")[-1]
                try:
                    total = int(total_part)
                    if total > 0:
                        return total
                except (TypeError, ValueError):
                    pass
        except Exception:
            # Ignore; return unknown size
            pass

        return 0

    if not recursive:
        # Single file download - check patterns
        filename = key.split('/')[-1] if '/' in key else key
        if not should_process_file(filename, list(include) if include else None, list(exclude) if exclude else None):
            error_message(f"Skipping {key} (excluded by pattern)")
            return
        
        # Determine final destination path:
        # - If destination points to an existing directory, or ends with '/', or is '.'/"./",
        #   download into that directory using the source filename.
        dest_is_dir_hint = destination.endswith('/') or destination in ('.', './')
        if dest_path.exists() and dest_path.is_dir():
            final_path = dest_path / filename
        elif dest_is_dir_hint:
            final_path = dest_path / filename
        else:
            final_path = dest_path
        
        final_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine remote size and existence before starting transfer
        try:
            file_size = _resolve_remote_size()
        except ObjectNotFoundError:
            raise COSError(f"Object not found: cos://{bucket}/{key}")

        if not no_progress:
            # Note: file_size may be 0 for unknown; progress will handle indeterminate totals

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(
                    f"Downloading {key}...", total=file_size or None
                )
                def on_update(done, _total):
                    progress.update(task, completed=done)
                try:
                    if file_size and file_size > 0:
                        from ..utils import parse_size_to_bytes, ResumeTracker
                        ps = parse_size_to_bytes(part_size)
                        # optional resume tracker
                        tracker = ResumeTracker() if resume else None
                        download_file_in_ranges_with_progress(
                            cos_client_raw,
                            bucket,
                            key,
                            final_path,
                            total_size=file_size,
                            chunk_size=ps,
                            progress_update=on_update,
                            resume=resume,
                            resume_tracker=tracker,
                            max_retries=max_retries,
                            retry_backoff=retry_backoff,
                            retry_backoff_max=retry_backoff_max,
                        )
                    else:
                        download_file_with_progress_polling(
                            cos_client_raw,
                            bucket,
                            key,
                            final_path,
                            total_size=file_size,
                            progress_update=on_update,
                        )
                except Exception as _e:
                    # Normalize any SDK error into a CLI error for consistent messaging
                    raise COSError(f"Failed to download cos://{bucket}/{key}: {_e}")
        else:
            cos_client.download_file(key, str(final_path))
        
        success_message(f"Downloaded cos://{bucket}/{key} to {str(final_path)}")
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

        # Aggregate total bytes for progress
        object_sizes = {obj.get("Key", ""): int(obj.get("Size", 0)) for obj in filtered_objects}
        total_bytes = sum(object_sizes.values())

        if not no_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(f"Downloading {len(filtered_objects)} files...", total=total_bytes)

                def do_download(obj):
                    obj_key = obj.get("Key", "")
                    rel_path = obj_key[len(key):].lstrip("/")
                    local_path = dest_path / rel_path
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    cos_client.download_file(obj_key, str(local_path))
                    progress.update(task, advance=object_sizes[obj_key])

                with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
                    futures = [executor.submit(do_download, obj) for obj in filtered_objects]
                    for fut in as_completed(futures):
                        exc = fut.exception()
                        if exc:
                            raise exc
        else:
            with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
                def do_download(obj):
                    obj_key = obj.get("Key", "")
                    rel_path = obj_key[len(key):].lstrip("/")
                    local_path = dest_path / rel_path
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    cos_client.download_file(obj_key, str(local_path))
                futures = [executor.submit(do_download, obj) for obj in filtered_objects]
                for fut in as_completed(futures):
                    exc = fut.exception()
                    if exc:
                        raise exc

        success_message(f"Downloaded {len(filtered_objects)} files to {destination}")


def _copy_objects(_ctx, cos_client_raw, source, destination, recursive, include, exclude, no_progress):
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

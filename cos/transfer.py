"""Streaming transfer utilities for COS CLI.

Provides per-file progress updates for downloads via file-size polling
and multipart uploads for large files with byte-level progress updates.

These functions are designed to be used by commands without exposing
low-level SDK details to the rest of the codebase.
"""

import threading
import time
from pathlib import Path
from typing import Callable, List, Tuple, Optional
from qcloud_cos.cos_exception import CosServiceError, CosClientError
from .utils import ResumeTracker


def download_file_with_progress_polling(
    client_raw,
    bucket: str,
    key: str,
    dest_path: Path,
    total_size: int,
    progress_update: Callable[[int, int], None],
    poll_interval: float = 0.1,
):
    """Download a file using SDK's download_file while polling local file size.

    Args:
        client_raw: Authenticated CosS3Client
        bucket: Bucket name
        key: Object key in COS
        dest_path: Destination local path
        total_size: Expected total size in bytes
        progress_update: Callback receiving (bytes_transferred, total_size)
        poll_interval: Polling interval seconds
    """

    stop_flag = threading.Event()
    bytes_holder = {"value": 0}

    def poller():
        while not stop_flag.is_set():
            try:
                if dest_path.exists():
                    sz = dest_path.stat().st_size
                    bytes_holder["value"] = sz
                    progress_update(sz, total_size)
            except (OSError, PermissionError):
                # Silent polling error; continue
                pass
            time.sleep(poll_interval)

    t = threading.Thread(target=poller, daemon=True)
    t.start()
    try:
        client_raw.download_file(
            Bucket=bucket,
            Key=key,
            DestFilePath=str(dest_path),
        )
    finally:
        stop_flag.set()
        t.join(timeout=1.0)
        # Ensure final completion
        progress_update(total_size, total_size)


def upload_file_multipart_with_progress(
    client_raw,
    bucket: str,
    key: str,
    local_path: Path,
    chunk_size: int,
    progress_update: Callable[[int, int], None],
    max_retries: int = 3,
    retry_backoff: float = 0.5,
    retry_backoff_max: float = 5.0,
):
    """Upload a local file using multipart API with byte-level progress.

    Args:
        client_raw: Authenticated CosS3Client
        bucket: Bucket name
        key: Object key in COS
        local_path: Local file path
        chunk_size: Size of each part in bytes (e.g., 8MB)
        progress_update: Callback receiving (bytes_transferred, total_size)
    """

    total_size = local_path.stat().st_size
    # Initiate multipart upload
    resp = client_raw.create_multipart_upload(Bucket=bucket, Key=key)
    upload_id = resp.get("UploadId")
    parts: List[Tuple[int, str]] = []  # (PartNumber, ETag)
    transferred = 0
    part_number = 1
    try:
        with open(local_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                # Retry upload_part with backoff
                attempt = 0
                while True:
                    try:
                        put = client_raw.upload_part(
                            Bucket=bucket,
                            Key=key,
                            PartNumber=part_number,
                            UploadId=upload_id,
                            Body=chunk,
                        )
                        break
                    except (OSError, CosServiceError, CosClientError) as _e:
                        if attempt >= max_retries:
                            raise
                        delay = min(retry_backoff * (2 ** attempt), retry_backoff_max)
                        time.sleep(delay)
                        attempt += 1
                etag = put.get("ETag")
                parts.append((part_number, etag))
                transferred += len(chunk)
                progress_update(transferred, total_size)
                part_number += 1
        # Complete
        client_raw.complete_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={
                "Part": [{"PartNumber": pn, "ETag": etag} for pn, etag in parts]
            },
        )
        # Ensure final completion
        progress_update(total_size, total_size)
    except (OSError, CosServiceError, CosClientError) as _e:
        # Attempt to abort only for expected SDK/client errors; ignore abort failures
        try:
            client_raw.abort_multipart_upload(
                Bucket=bucket, Key=key, UploadId=upload_id
            )
        except (OSError, CosServiceError, CosClientError):
            pass
        raise


def download_file_in_ranges_with_progress(
    client_raw,
    bucket: str,
    key: str,
    dest_path: Path,
    total_size: int,
    chunk_size: int,
    progress_update: Callable[[int, int], None],
    *,
    resume: bool = True,
    resume_tracker: Optional[ResumeTracker] = None,
    max_retries: int = 3,
    retry_backoff: float = 0.5,
    retry_backoff_max: float = 5.0,
):
    """Download a file via ranged GET requests with byte-level progress.

    Args:
        client_raw: Authenticated CosS3Client
        bucket: Bucket name
        key: Object key in COS
        dest_path: Destination local path
        total_size: Expected total size in bytes
        chunk_size: Size for each range in bytes
        progress_update: Callback receiving (bytes_transferred, total_size)
    """
    transferred = 0
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    # Determine resume offset
    start = 0
    if resume:
        if dest_path.exists():
            try:
                fs = dest_path.stat().st_size
                if 0 < fs < total_size:
                    start = fs
            except OSError:
                start = 0
        if resume_tracker is not None:
            try:
                st = resume_tracker.load_progress(str(dest_path), "download")
                if st and isinstance(st.get("data", {}), dict):
                    off = int(st["data"].get("offset", 0))
                    if 0 < off < total_size:
                        start = max(start, off)
            except Exception:
                pass

    # Open file in appropriate mode
    mode = "r+b" if dest_path.exists() and start > 0 else "wb"
    with open(dest_path, mode) as out:
        if start > 0:
            try:
                out.seek(start)
            except OSError:
                start = 0
                out.seek(0)
        while start < total_size:
            end = min(start + chunk_size - 1, total_size - 1)
            expected = end - start + 1
            rng = f"bytes={start}-{end}"
            # Retry ranged GET with backoff
            attempt = 0
            while True:
                try:
                    resp = client_raw.get_object(Bucket=bucket, Key=key, Range=rng)
                    break
                except Exception:
                    if attempt >= max_retries:
                        raise
                    delay = min(retry_backoff * (2 ** attempt), retry_backoff_max)
                    time.sleep(delay)
                    attempt += 1
            body = resp.get("Body")

            # Read exactly the expected number of bytes from the stream when possible
            if hasattr(body, "read"):
                remaining = expected
                buffers = []
                # Read in 1MB chunks or remaining size
                while remaining > 0:
                    chunk = body.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    buffers.append(chunk)
                    remaining -= len(chunk)
                data = b"".join(buffers)
            else:
                data = body

            if not data:
                # No data returned; treat as transient error for retry at next iteration
                # Sleep a minimal delay and continue (bounded by loop condition)
                delay = min(retry_backoff, retry_backoff_max)
                time.sleep(delay)
                continue

            out.write(data)
            transferred += len(data)
            progress_update(transferred, total_size)

            # Save resume progress
            if resume and resume_tracker is not None:
                try:
                    resume_tracker.save_progress(
                        str(dest_path), "download", {"offset": start + len(data), "total": total_size}
                    )
                except Exception:
                    pass

            # Advance start by the number of bytes actually written
            start += len(data)
    # Ensure completion
    progress_update(total_size, total_size)
    # Clear resume tracking on completion
    if resume and resume_tracker is not None:
        try:
            resume_tracker.clear_progress(str(dest_path), "download")
        except Exception:
            pass

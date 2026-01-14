from typing import Dict, Tuple

import io

from cos.transfer import (
    upload_file_multipart_with_progress,
    download_file_in_ranges_with_progress,
)


class FakeRawClient:
    def __init__(self):
        self.storage: Dict[str, Dict[str, bytes]] = {}
        self.multipart_store: Dict[Tuple[str, str, str], Dict[int, bytes]] = {}

    # Multipart upload methods
    def create_multipart_upload(self, Bucket: str, Key: str):
        upload_id = f"uid-{Bucket}-{Key}"
        self.multipart_store[(Bucket, Key, upload_id)] = {}
        return {"UploadId": upload_id}

    def upload_part(self, Bucket: str, Key: str, PartNumber: int, UploadId: str, Body: bytes):
        self.multipart_store[(Bucket, Key, UploadId)][PartNumber] = Body
        return {"ETag": f"\"etag-{PartNumber}\""}

    def complete_multipart_upload(self, Bucket: str, Key: str, UploadId: str, MultipartUpload: Dict):
        _ = MultipartUpload
        parts = self.multipart_store.pop((Bucket, Key, UploadId), {})
        ordered = [parts[pn] for pn in sorted(parts.keys())]
        data = b"".join(ordered)
        bucket = self.storage.setdefault(Bucket, {})
        bucket[Key] = data
        return {"ETag": "\"complete-etag\""}

    def abort_multipart_upload(self, Bucket: str, Key: str, UploadId: str):
        self.multipart_store.pop((Bucket, Key, UploadId), None)
        return {}

    # GET object (range)
    def get_object(self, Bucket: str, Key: str, Range: str):
        data = self.storage.get(Bucket, {}).get(Key, b"")
        # Range is like 'bytes=start-end'
        _, rng = Range.split("=")
        start_s, end_s = rng.split("-")
        start, end = int(start_s), int(end_s)
        slice_ = data[start : end + 1]
        return {"Body": io.BytesIO(slice_)}


def test_streaming_multipart_upload_and_range_download(tmp_path):
    client = FakeRawClient()
    bucket = "bucket"
    key = "large.bin"

    # Create a large local file (~10MB)
    local = tmp_path / "large.bin"
    chunk = b"0123456789abcdef" * 32768  # 512KB
    total_chunks = 20  # ~10MB
    with open(local, "wb") as f:
        for _ in range(total_chunks):
            f.write(chunk)
    total_size = local.stat().st_size

    # Track progress updates
    upload_progress = []
    def up_cb(done, total):
        upload_progress.append((done, total))

    # Multipart upload with progress
    upload_file_multipart_with_progress(
        client, bucket, key, local, chunk_size=1 * 1024 * 1024, progress_update=up_cb
    )

    # Verify server stored bytes
    assert client.storage[bucket][key] == local.read_bytes()
    assert upload_progress and upload_progress[-1][0] == total_size

    # Range download to new path
    dest = tmp_path / "download.bin"
    download_progress = []
    def down_cb(done, total):
        download_progress.append((done, total))

    download_file_in_ranges_with_progress(
        client, bucket, key, dest, total_size=total_size, chunk_size=1 * 1024 * 1024, progress_update=down_cb
    )

    assert dest.read_bytes() == local.read_bytes()
    assert download_progress and download_progress[-1][0] == total_size

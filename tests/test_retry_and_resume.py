import io
from pathlib import Path

from cos.transfer import download_file_in_ranges_with_progress, upload_file_multipart_with_progress
from cos.utils import ResumeTracker


class FlakyClient:
    def __init__(self, base_data: bytes):
        self.data = base_data
        self.fail_map = {}
        self.upload_parts = []

    # Multipart upload API
    def create_multipart_upload(self, Bucket: str, Key: str):
        self._bucket = Bucket
        self._key = Key
        self._parts = {}
        return {"UploadId": "uid"}

    def upload_part(self, Bucket: str, Key: str, PartNumber: int, UploadId: str, Body: bytes):
        self.upload_parts.append(PartNumber)
        return {"ETag": f'"etag-{PartNumber}"'}

    def complete_multipart_upload(self, Bucket: str, Key: str, UploadId: str, MultipartUpload):
        ordered = [self._parts.get(pn, b"") for pn in sorted(self._parts)]
        return {"ETag": '"complete"'}

    def abort_multipart_upload(self, Bucket: str, Key: str, UploadId: str):
        return {}

    # Ranged GET with controlled failures
    def get_object(self, Bucket: str, Key: str, Range: str):
        _, rng = Range.split("=")
        if self.fail_map.get(rng, 0) > 0:
            self.fail_map[rng] -= 1
            raise Exception("Transient error")
        start_s, end_s = rng.split("-")
        start, end = int(start_s), int(end_s)
        slice_ = self.data[start : end + 1]
        return {"Body": io.BytesIO(slice_)}


def test_ranged_download_retries_and_parts(tmp_path):
    # Prepare 5MB of data
    block = b"A" * (1024 * 1024)
    total = block * 5
    client = FlakyClient(total)
    # Fail first attempt for the second range 1MB-1.999MB
    client.fail_map["bytes=1048576-2097151"] = 1

    dest = tmp_path / "out.bin"
    progress = []
    def cb(done, total_sz):
        progress.append(done)

    download_file_in_ranges_with_progress(
        client,
        bucket="b",
        key="k",
        dest_path=dest,
        total_size=len(total),
        chunk_size=1024 * 1024,
        progress_update=cb,
        max_retries=2,
        retry_backoff=0.01,
        retry_backoff_max=0.05,
    )

    assert dest.read_bytes() == total
    # Expect at least 5 progress updates (one per part)
    assert max(progress) == len(total)


def test_resumable_download(tmp_path):
    # Prepare 3MB
    block = b"B" * (1024 * 1024)
    total = block * 3
    client = FlakyClient(total)

    dest = tmp_path / "resume.bin"
    # Write first 1MB to simulate a partial file
    with open(dest, "wb") as f:
        f.write(total[:1024 * 1024])

    tracker = ResumeTracker(cache_dir=tmp_path / ".cache")
    tracker.save_progress(str(dest), "download", {"offset": 1024 * 1024, "total": len(total)})

    progress = []
    def cb(done, total_sz):
        progress.append(done)

    download_file_in_ranges_with_progress(
        client,
        bucket="b",
        key="k",
        dest_path=dest,
        total_size=len(total),
        chunk_size=1024 * 1024,
        progress_update=cb,
        resume=True,
        resume_tracker=tracker,
        max_retries=1,
        retry_backoff=0.01,
        retry_backoff_max=0.05,
    )

    assert dest.read_bytes() == total
    # Ensure tracker cleared
    assert tracker.load_progress(str(dest), "download") is None
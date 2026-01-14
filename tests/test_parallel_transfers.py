import io
import os
from pathlib import Path
from typing import Dict, List

import pytest
from click.testing import CliRunner


class FakeRawClient:
    def __init__(self):
        self.storage: Dict[str, Dict[str, bytes]] = {}

    def upload_file(self, Bucket: str, LocalFilePath: str, Key: str, **kwargs):
        data = Path(LocalFilePath).read_bytes()
        bucket = self.storage.setdefault(Bucket, {})
        bucket[Key] = data
        return {"ETag": "\"fake-etag\""}

    def download_file(self, Bucket: str, Key: str, DestFilePath: str, **kwargs):
        data = self.storage.get(Bucket, {}).get(Key)
        if data is None:
            raise RuntimeError("NoSuchKey")
        Path(DestFilePath).parent.mkdir(parents=True, exist_ok=True)
        Path(DestFilePath).write_bytes(data)
        return {"ETag": "\"fake-etag\""}

    def list_objects(self, Bucket: str, Prefix: str = "", Delimiter: str = "", MaxKeys: int = 1000):
        objs: List[Dict] = []
        for key, data in self.storage.get(Bucket, {}).items():
            if key.startswith(Prefix):
                objs.append({"Key": key, "Size": len(data)})
        return {"Contents": objs}


class FakeCOSAuthenticator:
    def __init__(self, _):
        self.client = FakeRawClient()

    def authenticate(self, region=None):
        return self.client


class FakeCOSClient:
    def __init__(self, client: FakeRawClient, bucket: str = None):
        self.client = client
        self.bucket = bucket

    def upload_file(self, local_path: str, key: str, bucket: str = None, **kwargs):
        return self.client.upload_file(Bucket=self.bucket, LocalFilePath=local_path, Key=key)

    def download_file(self, key: str, local_path: str, bucket: str = None, **kwargs):
        return self.client.download_file(Bucket=self.bucket, Key=key, DestFilePath=local_path)

    def list_objects(self, bucket: str = None, prefix: str = "", delimiter: str = "", max_keys: int = 1000):
        return self.client.list_objects(Bucket=self.bucket, Prefix=prefix, Delimiter=delimiter, MaxKeys=max_keys)


def test_parallel_upload_and_download(monkeypatch, tmp_path):
    # Import cp after monkeypatching
    import cos.commands.cp as cp_mod

    # Patch authenticator and client wrapper
    monkeypatch.setattr(cp_mod, "COSAuthenticator", FakeCOSAuthenticator)
    monkeypatch.setattr(cp_mod, "COSClient", FakeCOSClient)

    # Create local files to upload
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    files = [src_dir / f"file_{i}.txt" for i in range(10)]
    for i, p in enumerate(files):
        p.write_bytes(f"data-{i}".encode())

    # Upload directory (recursive, concurrency)
    runner = CliRunner()
    result = runner.invoke(cp_mod.cp, [str(src_dir), "cos://bucket/upload/", "--recursive", "--concurrency", "4", "--no-progress"])
    assert result.exit_code == 0, result.output

    # Download directory back
    dest_dir = tmp_path / "dest"
    result = runner.invoke(cp_mod.cp, ["cos://bucket/upload/", str(dest_dir), "--recursive", "--concurrency", "4", "--no-progress"])
    assert result.exit_code == 0, result.output

    # Verify files
    for i in range(10):
        data = (dest_dir / f"file_{i}.txt").read_text()
        assert data == f"data-{i}"

"""Test configuration and shared fixtures for pytest"""

import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, MagicMock
from click.testing import CliRunner


# ============ CLI Testing ============

@pytest.fixture
def cli_runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


# ============ File System Fixtures ============

@pytest.fixture
def temp_config_dir():
    """Create temporary configuration directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmp = Path(tempfile.mkdtemp(prefix="cos_test_"))
    yield tmp
    if tmp.exists():
        shutil.rmtree(tmp)


@pytest.fixture
def temp_file(temp_dir):
    """Create a temporary test file."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Test content for COS operations")
    return file_path


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    files = {}
    
    # Create test files
    for i in range(3):
        file_path = temp_dir / f"file{i}.txt"
        content = f"Content of file {i}\n" * 10  # Make it bigger
        file_path.write_text(content)
        files[f"file{i}.txt"] = file_path
    
    # Create a subdirectory with files
    sub_dir = temp_dir / "subdir"
    sub_dir.mkdir()
    for i in range(2):
        file_path = sub_dir / f"subfile{i}.txt"
        content = f"Content of subfile {i}\n" * 5
        file_path.write_text(content)
        files[f"subdir/subfile{i}.txt"] = file_path
    
    return files


# ============ Mock Configuration ============

@pytest.fixture
def mock_credentials():
    """Mock credentials for testing"""
    return {
        "secret_id": "AKID_TEST_123456",
        "secret_key": "TEST_SECRET_KEY_123456",
        "assume_role": "qcs::cam::uin/100000000:roleName/TestRole",
    }


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "region": "ap-shanghai",
        "output": "json",
        "endpoint_url": None,
    }


@pytest.fixture
def mock_config_manager():
    """Create a mock ConfigManager."""
    config = Mock()
    config.get_config_value = Mock(side_effect=lambda key, default=None: {
        "bucket": "test-bucket",
        "prefix": "test-prefix/",
        "region": "ap-shanghai",
        "secret_id": "test-secret-id",
        "secret_key": "test-secret-key",
    }.get(key, default))
    config.profile = "default"
    return config


# ============ Mock COS Client ============

@pytest.fixture
def mock_cos_s3_client():
    """Create a mock COS S3 client (raw SDK client)."""
    client = MagicMock()
    client._conf = Mock()
    client._conf._region = "ap-shanghai"
    
    # Mock list_objects
    client.list_objects = Mock(return_value={
        "Contents": [
            {
                "Key": "test-prefix/file1.txt",
                "Size": 1024,
                "LastModified": "2024-01-01T12:00:00.000Z",
                "ETag": '"abc123"',
            },
            {
                "Key": "test-prefix/file2.txt",
                "Size": 2048,
                "LastModified": "2024-01-02T12:00:00.000Z",
                "ETag": '"def456"',
            },
        ],
        "CommonPrefixes": [
            {"Prefix": "test-prefix/folder1/"},
            {"Prefix": "test-prefix/folder2/"},
        ],
    })
    
    # Mock other operations
    client.upload_file = Mock(return_value={"ETag": '"uploaded123"'})
    client.download_file = Mock(return_value={})
    client.delete_object = Mock(return_value={})
    client.copy_object = Mock(return_value={"ETag": '"copied123"'})
    client.get_presigned_url = Mock(return_value="https://test-bucket.cos.ap-shanghai.myqcloud.com/test-key?sign=xxx")
    
    return client


@pytest.fixture
def mock_cos_client(mock_cos_s3_client):
    """Create a mock COSClient wrapper."""
    client = Mock()
    client.client = mock_cos_s3_client
    client.bucket = "test-bucket"
    
    # Delegate methods to raw client
    client.list_objects = Mock(return_value=mock_cos_s3_client.list_objects.return_value)
    client.upload_file = Mock(return_value=mock_cos_s3_client.upload_file.return_value)
    client.download_file = Mock(return_value=mock_cos_s3_client.download_file.return_value)
    client.delete_object = Mock(return_value=mock_cos_s3_client.delete_object.return_value)
    client.copy_object = Mock(return_value=mock_cos_s3_client.copy_object.return_value)
    
    return client


@pytest.fixture
def mock_authenticator(mock_cos_s3_client):
    """Create a mock COSAuthenticator."""
    authenticator = Mock()
    authenticator.authenticate = Mock(return_value=mock_cos_s3_client)
    return authenticator


# ============ Mock Data ============

@pytest.fixture
def mock_buckets():
    """Mock bucket list data."""
    return [
        {
            "Name": "test-bucket-1",
            "Location": "ap-shanghai",
            "CreationDate": "2024-01-01T00:00:00.000Z",
        },
        {
            "Name": "test-bucket-2",
            "Location": "ap-beijing",
            "CreationDate": "2024-01-02T00:00:00.000Z",
        },
        {
            "Name": "test-bucket-3",
            "Location": "ap-guangzhou",
            "CreationDate": "2024-01-03T00:00:00.000Z",
        },
    ]

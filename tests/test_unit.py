"""
Unit tests for COS CLI utility functions and helpers.

These tests validate core functionality without requiring external dependencies.
"""

import pytest
from pathlib import Path
from datetime import datetime

from cos.utils import (
    parse_cos_uri,
    is_cos_uri,
    format_size,
    format_datetime,
    get_file_md5,
)
from cos.exceptions import COSError


class TestCOSURIParsing:
    """Test COS URI parsing utilities."""
    
    def test_parse_valid_uri(self):
        """Test parsing a valid COS URI."""
        bucket, key = parse_cos_uri("cos://my-bucket/path/to/file.txt")
        assert bucket == "my-bucket"
        assert key == "path/to/file.txt"
    
    def test_parse_uri_with_trailing_slash(self):
        """Test parsing URI with trailing slash."""
        bucket, key = parse_cos_uri("cos://my-bucket/path/to/folder/")
        assert bucket == "my-bucket"
        assert key == "path/to/folder/"
    
    def test_parse_uri_bucket_only(self):
        """Test parsing URI with bucket only."""
        bucket, key = parse_cos_uri("cos://my-bucket")
        assert bucket == "my-bucket"
        assert key == ""
    
    def test_parse_uri_bucket_with_slash(self):
        """Test parsing URI with bucket and trailing slash."""
        bucket, key = parse_cos_uri("cos://my-bucket/")
        assert bucket == "my-bucket"
        assert key == ""
    
    def test_is_cos_uri_valid(self):
        """Test identifying valid COS URIs."""
        assert is_cos_uri("cos://bucket/key") is True
        assert is_cos_uri("cos://bucket") is True
        assert is_cos_uri("cos://bucket/") is True
    
    def test_is_cos_uri_invalid(self):
        """Test identifying invalid COS URIs."""
        assert is_cos_uri("/local/path") is False
        assert is_cos_uri("./relative/path") is False
        assert is_cos_uri("http://example.com") is False
        assert is_cos_uri("s3://bucket/key") is False


class TestFormatting:
    """Test formatting utilities."""
    
    def test_format_size_bytes(self):
        """Test formatting bytes."""
        assert format_size(0) == "0.0 B"
        assert format_size(512) == "512.0 B"
        assert format_size(1023) == "1023.0 B"
    
    def test_format_size_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_size(1024) == "1.0 KB"
        assert format_size(1536) == "1.5 KB"
        assert format_size(2048) == "2.0 KB"
    
    def test_format_size_megabytes(self):
        """Test formatting megabytes."""
        assert format_size(1024 * 1024) == "1.0 MB"
        assert format_size(1024 * 1024 * 1.5) == "1.5 MB"
    
    def test_format_size_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_size(1024 * 1024 * 1024 * 2.5) == "2.5 GB"
    
    def test_format_size_string_input(self):
        """Test formatting with string input (should convert)."""
        assert format_size("1024") == "1.0 KB"
        assert format_size("2048") == "2.0 KB"
    
    def test_format_datetime_iso_format(self):
        """Test formatting ISO datetime strings."""
        result = format_datetime("2024-01-15T10:30:00.000Z")
        assert "2024-01-15" in result
        assert "10:30" in result
    
    def test_format_datetime_common_format(self):
        """Test formatting common datetime strings."""
        result = format_datetime("2024-01-15 10:30:00")
        assert "2024-01-15" in result
    
    def test_format_datetime_datetime_object(self):
        """Test formatting datetime objects."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = format_datetime(dt)
        assert "2024-01-15" in result
        assert "10:30" in result


class TestFileOperations:
    """Test file operation utilities."""
    
    def test_get_file_md5(self, temp_file):
        """Test getting file MD5 hash."""
        hash1 = get_file_md5(str(temp_file))
        assert hash1 is not None
        assert len(hash1) == 32  # MD5 hash length
        
        # Same file should produce same hash
        hash2 = get_file_md5(str(temp_file))
        assert hash1 == hash2
    
    def test_get_file_md5_different_content(self, temp_dir):
        """Test that different files produce different hashes."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        
        file1.write_text("Content A")
        file2.write_text("Content B")
        
        hash1 = get_file_md5(str(file1))
        hash2 = get_file_md5(str(file2))
        
        assert hash1 != hash2
    
    def test_get_file_md5_nonexistent(self):
        """Test MD5 of nonexistent file."""
        with pytest.raises(FileNotFoundError):
            get_file_md5("/nonexistent/file.txt")


class TestCommandImports:
    """Test that all command modules can be imported."""
    
    def test_import_ls_command(self):
        """Test importing ls command."""
        from cos.commands.ls import ls
        assert ls is not None
        assert callable(ls)
    
    def test_import_cp_command(self):
        """Test importing cp command."""
        from cos.commands.cp import cp
        assert cp is not None
        assert callable(cp)
    
    def test_import_mv_command(self):
        """Test importing mv command."""
        from cos.commands.mv import mv
        assert mv is not None
        assert callable(mv)
    
    def test_import_rm_command(self):
        """Test importing rm command."""
        from cos.commands.rm import rm
        assert rm is not None
        assert callable(rm)
    
    def test_import_presign_command(self):
        """Test importing presign command."""
        from cos.commands.presign import presign
        assert presign is not None
        assert callable(presign)
    
    def test_import_sync_command(self):
        """Test importing sync command."""
        from cos.commands.sync import sync
        assert sync is not None
        assert callable(sync)
    
    def test_import_mb_command(self):
        """Test importing mb (make bucket) command."""
        from cos.commands.mb import mb
        assert mb is not None
        assert callable(mb)
    
    def test_import_rb_command(self):
        """Test importing rb (remove bucket) command."""
        from cos.commands.rb import rb
        assert rb is not None
        assert callable(rb)


class TestMockingInfrastructure:
    """Test that mocking infrastructure works correctly."""
    
    def test_mock_cos_client_creation(self, mock_cos_client):
        """Test creating a mock COS client."""
        assert mock_cos_client is not None
        assert mock_cos_client.bucket == "test-bucket"
    
    def test_mock_list_objects(self, mock_cos_client):
        """Test mock list_objects returns expected data."""
        result = mock_cos_client.list_objects()
        assert "Contents" in result
        assert len(result["Contents"]) == 2
        assert result["Contents"][0]["Key"] == "test-prefix/file1.txt"
    
    def test_mock_authenticator(self, mock_authenticator, mock_cos_s3_client):
        """Test mock authenticator returns client."""
        client = mock_authenticator.authenticate()
        assert client is mock_cos_s3_client
    
    def test_mock_config_manager(self, mock_config_manager):
        """Test mock config manager."""
        assert mock_config_manager.get_config_value("bucket") == "test-bucket"
        assert mock_config_manager.get_config_value("region") == "ap-shanghai"
        assert mock_config_manager.get_config_value("nonexistent") is None


class TestTempFiles:
    """Test temporary file fixtures."""
    
    def test_temp_file_exists(self, temp_file):
        """Test temp file fixture creates a file."""
        assert temp_file.exists()
        assert temp_file.is_file()
        content = temp_file.read_text()
        assert len(content) > 0
    
    def test_temp_dir_exists(self, temp_dir):
        """Test temp dir fixture creates a directory."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()
    
    def test_sample_files(self, sample_files):
        """Test sample files fixture."""
        assert len(sample_files) == 5  # 3 files + 2 subfiles
        
        # Check main files
        for i in range(3):
            key = f"file{i}.txt"
            assert key in sample_files
            assert sample_files[key].exists()
        
        # Check subfiles
        for i in range(2):
            key = f"subdir/subfile{i}.txt"
            assert key in sample_files
            assert sample_files[key].exists()

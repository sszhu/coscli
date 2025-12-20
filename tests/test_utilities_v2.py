"""Tests for new utility functions: pattern matching, throttling, checksums"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from cos.utils import (
    matches_pattern,
    should_process_file,
    BandwidthThrottle,
    ResumeTracker,
    compute_file_checksum,
    compare_checksums,
)


class TestPatternMatching:
    """Test pattern matching utilities"""
    
    def test_matches_pattern_simple(self):
        """Test simple pattern matching"""
        assert matches_pattern("file.txt", ["*.txt"], is_include=True)
        assert not matches_pattern("file.pdf", ["*.txt"], is_include=True)
    
    def test_matches_pattern_multiple(self):
        """Test multiple patterns"""
        patterns = ["*.txt", "*.md", "*.py"]
        assert matches_pattern("file.txt", patterns, is_include=True)
        assert matches_pattern("README.md", patterns, is_include=True)
        assert matches_pattern("script.py", patterns, is_include=True)
        assert not matches_pattern("file.pdf", patterns, is_include=True)
    
    def test_matches_pattern_path(self):
        """Test pattern matching with paths"""
        assert matches_pattern("logs/app.log", ["*.log"], is_include=True)
        assert matches_pattern("logs/app.log", ["logs/*"], is_include=True)
    
    def test_matches_pattern_empty(self):
        """Test with empty patterns"""
        assert matches_pattern("any_file.txt", [], is_include=True)
        assert not matches_pattern("any_file.txt", [], is_include=False)
    
    def test_should_process_file_no_patterns(self):
        """Test processing with no patterns"""
        assert should_process_file("file.txt", None, None)
    
    def test_should_process_file_include_only(self):
        """Test processing with include patterns only"""
        include = ["*.txt", "*.md"]
        assert should_process_file("file.txt", include, None)
        assert should_process_file("README.md", include, None)
        assert not should_process_file("file.pdf", include, None)
    
    def test_should_process_file_exclude_only(self):
        """Test processing with exclude patterns only"""
        exclude = ["*.log", "*.tmp"]
        assert should_process_file("file.txt", None, exclude)
        assert not should_process_file("app.log", None, exclude)
        assert not should_process_file("temp.tmp", None, exclude)
    
    def test_should_process_file_include_and_exclude(self):
        """Test processing with both include and exclude patterns"""
        include = ["*.txt"]
        exclude = ["test_*.txt"]
        
        assert should_process_file("file.txt", include, exclude)
        assert not should_process_file("test_file.txt", include, exclude)
        assert not should_process_file("file.pdf", include, exclude)
    
    def test_should_process_file_complex(self):
        """Test complex pattern combinations"""
        include = ["*.py", "*.txt"]
        exclude = ["test_*", "*_test.py"]
        
        assert should_process_file("main.py", include, exclude)
        assert should_process_file("README.txt", include, exclude)
        assert not should_process_file("test_main.py", include, exclude)
        assert not should_process_file("main_test.py", include, exclude)
        assert not should_process_file("file.pdf", include, exclude)


class TestBandwidthThrottle:
    """Test bandwidth throttling"""
    
    def test_throttle_initialization(self):
        """Test throttle initialization"""
        throttle = BandwidthThrottle(max_bytes_per_sec=1024 * 1024)
        assert throttle.max_bytes_per_sec == 1024 * 1024
        assert throttle.bytes_transferred == 0
    
    def test_throttle_no_limit(self):
        """Test throttle with no limit"""
        throttle = BandwidthThrottle(max_bytes_per_sec=None)
        start_time = time.time()
        throttle.throttle(1024 * 1024)  # 1MB
        elapsed = time.time() - start_time
        assert elapsed < 0.1  # Should be instant
    
    def test_throttle_with_limit(self):
        """Test throttle with limit"""
        # 1MB per second limit
        throttle = BandwidthThrottle(max_bytes_per_sec=1024 * 1024)
        
        # Transfer 512KB - should take ~0.5s
        start_time = time.time()
        throttle.throttle(512 * 1024)
        elapsed = time.time() - start_time
        # With 1MB/s limit, 512KB should take ~0.5s (with some tolerance)
        assert 0.4 < elapsed < 0.7
        
        # Transfer another 512KB - total should be ~1s
        throttle.throttle(512 * 1024)
        total_elapsed = time.time() - start_time
        # Total time for 1MB at 1MB/s should be ~1s (with tolerance)
        assert 0.9 < total_elapsed < 1.3
    
    def test_get_speed(self):
        """Test speed calculation"""
        throttle = BandwidthThrottle(max_bytes_per_sec=None)
        throttle.bytes_transferred = 1024 * 1024  # 1MB
        throttle.start_time = time.time() - 1.0  # 1 second ago
        
        speed = throttle.get_speed()
        assert 900000 < speed < 1100000  # ~1MB/s with tolerance


class TestResumeTracker:
    """Test resume capability tracker"""
    
    def test_resume_tracker_initialization(self):
        """Test tracker initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".cos" / "cache"
            tracker = ResumeTracker(cache_dir)
            assert tracker.cache_dir == cache_dir
            assert cache_dir.exists()
    
    def test_save_and_load_progress(self):
        """Test saving and loading progress"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".cos" / "cache"
            tracker = ResumeTracker(cache_dir)
            
            # Save progress
            progress_data = {
                'bytes_transferred': 1024 * 1024,
                'total_bytes': 10 * 1024 * 1024,
                'part_number': 5
            }
            tracker.save_progress("test_file.bin", "upload", progress_data)
            
            # Load progress
            loaded = tracker.load_progress("test_file.bin", "upload")
            assert loaded is not None
            assert loaded['data'] == progress_data
            assert loaded['file_path'] == "test_file.bin"
            assert loaded['operation'] == "upload"
    
    def test_load_nonexistent_progress(self):
        """Test loading non-existent progress"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".cos" / "cache"
            tracker = ResumeTracker(cache_dir)
            
            result = tracker.load_progress("nonexistent.bin", "upload")
            assert result is None
    
    def test_clear_progress(self):
        """Test clearing progress"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".cos" / "cache"
            tracker = ResumeTracker(cache_dir)
            
            # Save and clear
            tracker.save_progress("test.bin", "upload", {'test': 'data'})
            tracker.clear_progress("test.bin", "upload")
            
            # Should be gone
            result = tracker.load_progress("test.bin", "upload")
            assert result is None


class TestChecksumFunctions:
    """Test checksum computation and comparison"""
    
    def test_compute_file_checksum_md5(self):
        """Test MD5 checksum computation"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Hello, World!")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path, "md5")
            # "Hello, World!" MD5 hash
            expected = "65a8e27d8879283831b664bd8b7f0ad4"
            assert checksum == expected
        finally:
            Path(temp_path).unlink()
    
    def test_compute_file_checksum_sha256(self):
        """Test SHA256 checksum computation"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Hello, World!")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path, "sha256")
            # "Hello, World!" SHA256 hash
            expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            assert checksum == expected
        finally:
            Path(temp_path).unlink()
    
    def test_compute_file_checksum_invalid_algorithm(self):
        """Test with invalid algorithm"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"test")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported algorithm"):
                compute_file_checksum(temp_path, "invalid")
        finally:
            Path(temp_path).unlink()
    
    def test_compare_checksums_match(self):
        """Test checksum comparison with match"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Hello, World!")
            temp_path = f.name
        
        try:
            # MD5 of "Hello, World!"
            remote_etag = "65a8e27d8879283831b664bd8b7f0ad4"
            assert compare_checksums(temp_path, remote_etag)
        finally:
            Path(temp_path).unlink()
    
    def test_compare_checksums_mismatch(self):
        """Test checksum comparison with mismatch"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Hello, World!")
            temp_path = f.name
        
        try:
            remote_etag = "different_hash"
            assert not compare_checksums(temp_path, remote_etag)
        finally:
            Path(temp_path).unlink()
    
    def test_compare_checksums_with_quotes(self):
        """Test checksum comparison with quoted ETag"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Hello, World!")
            temp_path = f.name
        
        try:
            # ETag with quotes (as returned by S3/COS)
            remote_etag = '"65a8e27d8879283831b664bd8b7f0ad4"'
            assert compare_checksums(temp_path, remote_etag)
        finally:
            Path(temp_path).unlink()
    
    def test_compare_checksums_multipart(self):
        """Test checksum comparison with multipart upload ETag"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"test")
            temp_path = f.name
        
        try:
            # Multipart ETag contains dash
            remote_etag = "d8e8fca2dc0f896fd7cb4cb0031ba249-5"
            # Should return False as multipart ETags can't be compared
            assert not compare_checksums(temp_path, remote_etag)
        finally:
            Path(temp_path).unlink()


class TestUtilityIntegration:
    """Integration tests for utilities"""
    
    def test_pattern_matching_with_real_files(self):
        """Test pattern matching with real file structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create test files
            (tmppath / "file1.txt").touch()
            (tmppath / "file2.py").touch()
            (tmppath / "test_file.py").touch()
            (tmppath / "README.md").touch()
            
            # Test include pattern
            files = list(tmppath.glob("*"))
            txt_files = [f for f in files if should_process_file(f.name, ["*.txt", "*.md"], None)]
            assert len(txt_files) == 2
            
            # Test exclude pattern
            py_files = [f for f in files if should_process_file(f.name, ["*.py"], ["test_*"])]
            assert len(py_files) == 1
            assert py_files[0].name == "file2.py"
    
    def test_checksum_workflow(self):
        """Test complete checksum workflow"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Test data for upload")
            temp_path = f.name
        
        try:
            # Compute checksum
            local_checksum = compute_file_checksum(temp_path, "md5")
            
            # Simulate COS upload and returned ETag
            remote_etag = local_checksum  # In reality, this comes from COS response
            
            # Verify upload
            assert compare_checksums(temp_path, remote_etag)
            
            # Modify file
            with open(temp_path, 'ab') as f:
                f.write(b" modified")
            
            # Should not match anymore
            assert not compare_checksums(temp_path, remote_etag)
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

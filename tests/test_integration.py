#!/usr/bin/env python3
"""
Integration Tests for COS CLI Commands

These are REAL tests that perform actual operations against COS.
Make sure you have proper credentials configured before running.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import time
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cos.config import ConfigManager
from cos.auth import COSAuthenticator
from cos.client import COSClient
from cos.utils import parse_cos_uri, format_size


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class IntegrationTestRunner:
    """Run integration tests against real COS"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_prefix = None  # Will be set in setup()
        self.temp_dir = None
        self.cos_client = None
        self.bucket = None
        
    def setup(self):
        """Setup test environment"""
        print(f"\n{Colors.BLUE}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}COS CLI Integration Tests{Colors.RESET}")
        print(f"{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")
        
        # Get COS client
        try:
            config_manager = ConfigManager()
            authenticator = COSAuthenticator(config_manager)
            cos_client_raw = authenticator.authenticate()
            
            # Get bucket from config
            self.bucket = config_manager.get_config_value("bucket")
            if not self.bucket:
                raise ValueError("No bucket configured. Run 'cos configure' first.")
            
            # Get prefix from config (where we have write access)
            base_prefix = config_manager.get_config_value("prefix", "")
            if base_prefix:
                self.test_prefix = f"{base_prefix.rstrip('/')}/integration-test-{int(time.time())}/"
            else:
                self.test_prefix = f"integration-test-{int(time.time())}/"
            
            self.cos_client = COSClient(cos_client_raw, self.bucket)
            
            print(f"{Colors.GREEN}✓{Colors.RESET} Connected to COS")
            print(f"  Bucket: {self.bucket}")
            print(f"  Test prefix: {self.test_prefix}\n")
            
        except Exception as e:
            print(f"{Colors.RED}✗ Failed to setup COS client: {e}{Colors.RESET}")
            sys.exit(1)
        
        # Create temp directory
        self.temp_dir = tempfile.mkdtemp(prefix="cos_integration_test_")
        print(f"{Colors.GREEN}✓{Colors.RESET} Created temp directory: {self.temp_dir}\n")
    
    def teardown(self):
        """Cleanup test environment"""
        print(f"\n{Colors.BLUE}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}Cleanup{Colors.RESET}")
        print(f"{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")
        
        # Delete all test files in COS
        try:
            print(f"Cleaning up COS objects with prefix: {self.test_prefix}")
            response = self.cos_client.list_objects(prefix=self.test_prefix, delimiter="")
            objects = response.get("Contents", [])
            
            deleted = 0
            for obj in objects:
                self.cos_client.delete_object(obj["Key"])
                deleted += 1
            
            print(f"{Colors.GREEN}✓{Colors.RESET} Deleted {deleted} test objects from COS\n")
        except Exception as e:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Warning: Failed to cleanup COS: {e}\n")
        
        # Delete temp directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"{Colors.GREEN}✓{Colors.RESET} Deleted temp directory\n")
        
        # Print summary
        print(f"{Colors.BLUE}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}Test Summary{Colors.RESET}")
        print(f"{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")
        
        total = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests:  {total}")
        print(f"{Colors.GREEN}Passed:       {self.tests_passed}{Colors.RESET}")
        if self.tests_failed > 0:
            print(f"{Colors.RED}Failed:       {self.tests_failed}{Colors.RESET}")
        else:
            print(f"Failed:       {self.tests_failed}")
        print(f"Success Rate: {success_rate:.1f}%\n")
        
        if self.tests_failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.RESET}\n")
            sys.exit(0)
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.RESET}\n")
            sys.exit(1)
    
    def run_test(self, name, test_func):
        """Run a single test"""
        print(f"{Colors.BOLD}Testing: {name}{Colors.RESET}")
        try:
            test_func()
            print(f"{Colors.GREEN}✓ PASS{Colors.RESET}\n")
            self.tests_passed += 1
        except AssertionError as e:
            print(f"{Colors.RED}✗ FAIL: {e}{Colors.RESET}\n")
            self.tests_failed += 1
        except Exception as e:
            print(f"{Colors.RED}✗ ERROR: {e}{Colors.RESET}\n")
            self.tests_failed += 1
    
    # ======================== TESTS ========================
    
    def test_upload_file(self):
        """Test uploading a file to COS"""
        # Create test file
        test_file = Path(self.temp_dir) / "test_upload.txt"
        test_content = "Hello, COS! This is a test file."
        test_file.write_text(test_content)
        
        # Upload
        key = f"{self.test_prefix}test_upload.txt"
        self.cos_client.upload_file(str(test_file), key)
        print(f"  Uploaded: {test_file.name} -> {key}")
        
        # Verify upload by listing
        response = self.cos_client.list_objects(prefix=self.test_prefix)
        objects = response.get("Contents", [])
        
        # Find our specific file
        our_file = [obj for obj in objects if obj["Key"] == key]
        assert len(our_file) == 1, f"File not found in COS after upload. Found {len(objects)} objects in prefix."
        
        # Check size (convert to int if it's a string)
        actual_size = our_file[0]["Size"]
        if isinstance(actual_size, str):
            actual_size = int(actual_size)
        print(f"  Size: {actual_size} bytes")
        assert actual_size > 0, "File size should be greater than 0"
    
    def test_download_file(self):
        """Test downloading a file from COS"""
        # Create and upload test file
        test_content = "Download test content"
        key = f"{self.test_prefix}test_download.txt"
        
        # Create temp file and upload
        upload_file = Path(self.temp_dir) / "upload.txt"
        upload_file.write_text(test_content)
        self.cos_client.upload_file(str(upload_file), key)
        
        # Download to different location
        download_file = Path(self.temp_dir) / "download.txt"
        self.cos_client.download_file(key, str(download_file))
        print(f"  Downloaded: {key} -> {download_file.name}")
        
        # Verify content
        downloaded_content = download_file.read_text()
        assert downloaded_content == test_content, "Downloaded content doesn't match"
    
    def test_list_objects(self):
        """Test listing objects in COS"""
        # Upload multiple files
        files = ["file1.txt", "file2.txt", "file3.txt"]
        for filename in files:
            test_file = Path(self.temp_dir) / filename
            test_file.write_text(f"Content of {filename}")
            key = f"{self.test_prefix}{filename}"
            self.cos_client.upload_file(str(test_file), key)
        
        # List objects with the full test prefix
        response = self.cos_client.list_objects(prefix=self.test_prefix)
        all_objects = response.get("Contents", [])
        
        # Filter to only the files we just uploaded (not other test files)
        test_files = [obj for obj in all_objects if any(obj["Key"].endswith(f) for f in files)]
        
        print(f"  Found {len(test_files)} of our test objects (total {len(all_objects)} in prefix)")
        assert len(test_files) == len(files), f"Expected {len(files)} objects, found {len(test_files)}"
        
        # Verify all files are listed
        keys = [obj["Key"] for obj in test_files]
        for filename in files:
            assert any(filename in k for k in keys), f"File {filename} not found in listing"
    
    def test_delete_object(self):
        """Test deleting an object from COS"""
        # Upload test file
        test_file = Path(self.temp_dir) / "test_delete.txt"
        test_file.write_text("This file will be deleted")
        key = f"{self.test_prefix}test_delete.txt"
        self.cos_client.upload_file(str(test_file), key)
        
        # Verify it exists
        response = self.cos_client.list_objects(prefix=key)
        assert len(response.get("Contents", [])) == 1, "File not found before deletion"
        
        # Delete
        self.cos_client.delete_object(key)
        print(f"  Deleted: {key}")
        
        # Verify deletion
        response = self.cos_client.list_objects(prefix=key)
        assert len(response.get("Contents", [])) == 0, "File still exists after deletion"
    
    def test_copy_object(self):
        """Test copying an object within COS"""
        # Upload source file
        test_file = Path(self.temp_dir) / "test_copy_source.txt"
        test_content = "Content to copy"
        test_file.write_text(test_content)
        
        source_key = f"{self.test_prefix}copy_source.txt"
        dest_key = f"{self.test_prefix}copy_dest.txt"
        
        self.cos_client.upload_file(str(test_file), source_key)
        
        # Copy (requires bucket names)
        self.cos_client.copy_object(self.bucket, source_key, self.bucket, dest_key)
        print(f"  Copied: {source_key} -> {dest_key}")
        
        # Verify both files exist
        response = self.cos_client.list_objects(prefix=self.test_prefix)
        keys = [obj["Key"] for obj in response.get("Contents", [])]
        
        assert source_key in keys, "Source file not found after copy"
        assert dest_key in keys, "Destination file not found after copy"
        
        # Verify content by downloading
        download_file = Path(self.temp_dir) / "copied.txt"
        self.cos_client.download_file(dest_key, str(download_file))
        assert download_file.read_text() == test_content, "Copied content doesn't match"
    
    def test_presigned_url(self):
        """Test generating presigned URLs"""
        # Upload test file
        test_file = Path(self.temp_dir) / "test_presign.txt"
        test_content = "Presigned URL test"
        test_file.write_text(test_content)
        key = f"{self.test_prefix}test_presign.txt"
        
        self.cos_client.upload_file(str(test_file), key)
        
        # Generate presigned URL using base client
        url = self.cos_client.client.get_presigned_url(
            Method='GET',
            Bucket=self.bucket,
            Key=key,
            Expired=3600
        )
        print(f"  Generated presigned URL (valid for 1 hour)")
        print(f"  URL length: {len(url)} characters")
        
        assert url.startswith("https://"), "Invalid URL format"
    
    def test_upload_with_metadata(self):
        """Test uploading with custom metadata"""
        # Create test file
        test_file = Path(self.temp_dir) / "test_metadata.txt"
        test_file.write_text("File with metadata")
        key = f"{self.test_prefix}test_metadata.txt"
        
        # Upload with metadata
        metadata = {
            "author": "integration-test",
            "version": "1.0"
        }
        self.cos_client.upload_file(str(test_file), key, Metadata=metadata)
        print(f"  Uploaded with metadata: {metadata}")
        
        # Verify the upload succeeded by checking file exists
        response = self.cos_client.list_objects(prefix=self.test_prefix)
        keys = [obj["Key"] for obj in response.get("Contents", [])]
        assert key in keys, "File not found after upload with metadata"
    
    def test_list_with_prefix(self):
        """Test listing with prefix filtering"""
        # Create directory structure
        files = {
            "dir1/file1.txt": "Content 1",
            "dir1/file2.txt": "Content 2",
            "dir2/file3.txt": "Content 3",
        }
        
        for rel_path, content in files.items():
            test_file = Path(self.temp_dir) / rel_path.replace("/", "_")
            test_file.write_text(content)
            key = f"{self.test_prefix}{rel_path}"
            self.cos_client.upload_file(str(test_file), key)
        
        # List with prefix
        prefix = f"{self.test_prefix}dir1/"
        response = self.cos_client.list_objects(prefix=prefix)
        objects = response.get("Contents", [])
        
        print(f"  Listed with prefix '{prefix}': found {len(objects)} objects")
        assert len(objects) == 2, f"Expected 2 objects with prefix dir1/, found {len(objects)}"
        
        for obj in objects:
            assert obj["Key"].startswith(prefix), f"Object key {obj['Key']} doesn't start with prefix"
    
    def test_batch_operations(self):
        """Test batch upload and delete"""
        # Upload multiple files
        num_files = 5
        keys = []
        
        print(f"  Uploading {num_files} files...")
        for i in range(num_files):
            test_file = Path(self.temp_dir) / f"batch_{i}.txt"
            test_file.write_text(f"Batch content {i}")
            key = f"{self.test_prefix}batch/batch_{i}.txt"
            self.cos_client.upload_file(str(test_file), key)
            keys.append(key)
        
        # Verify all uploaded
        response = self.cos_client.list_objects(prefix=f"{self.test_prefix}batch/")
        objects = response.get("Contents", [])
        assert len(objects) == num_files, f"Expected {num_files} files, found {len(objects)}"
        
        # Batch delete
        print(f"  Deleting {num_files} files...")
        for key in keys:
            self.cos_client.delete_object(key)
        
        # Verify all deleted
        response = self.cos_client.list_objects(prefix=f"{self.test_prefix}batch/")
        assert len(response.get("Contents", [])) == 0, "Some files still exist after batch delete"
    
    def run_all_tests(self):
        """Run all integration tests"""
        self.setup()
        
        try:
            self.run_test("Upload File", self.test_upload_file)
            self.run_test("Download File", self.test_download_file)
            self.run_test("List Objects", self.test_list_objects)
            self.run_test("Delete Object", self.test_delete_object)
            self.run_test("Copy Object", self.test_copy_object)
            self.run_test("Presigned URL", self.test_presigned_url)
            self.run_test("Upload with Metadata", self.test_upload_with_metadata)
            self.run_test("List with Prefix", self.test_list_with_prefix)
            self.run_test("Batch Operations", self.test_batch_operations)
            
        finally:
            self.teardown()


if __name__ == "__main__":
    runner = IntegrationTestRunner()
    runner.run_all_tests()

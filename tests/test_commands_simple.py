"""Simple test runner for COS CLI commands without pytest dependency"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cos.commands.ls import ls
from cos.commands.cp import cp
from cos.commands.mv import mv
from cos.commands.rm import rm
from cos.commands.presign import presign
from cos.commands.sync import sync


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"❌ FAIL: {test_name}")
        print(f"   Error: {str(error)}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Results: {self.passed} passed, {self.failed} failed out of {total}")
        print(f"{'='*60}")
        return self.failed == 0


def run_test(test_func, result):
    """Run a single test function"""
    test_name = test_func.__name__
    try:
        test_func()
        result.add_pass(test_name)
    except Exception as e:
        result.add_fail(test_name, e)
        if '--verbose' in sys.argv:
            traceback.print_exc()


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_mock_cos_client_creation():
    """Test that we can create mock COS client"""
    client = Mock()
    client.list_buckets = Mock(return_value=[
        {"Name": "test-bucket", "Location": "ap-shanghai", "CreationDate": "2024-01-01"}
    ])
    buckets = client.list_buckets()
    assert len(buckets) == 1
    assert buckets[0]["Name"] == "test-bucket"


def test_mock_list_objects():
    """Test mocking list objects"""
    client = Mock()
    client.list_objects = Mock(return_value={
        "Contents": [
            {"Key": "file1.txt", "Size": 1024},
            {"Key": "file2.txt", "Size": 2048},
        ]
    })
    result = client.list_objects()
    assert len(result["Contents"]) == 2


def test_temp_file_creation():
    """Test creating temporary files"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    assert os.path.exists(temp_path)
    with open(temp_path) as f:
        content = f.read()
    assert content == "test content"
    
    os.unlink(temp_path)
    assert not os.path.exists(temp_path)


def test_temp_dir_with_files():
    """Test creating temporary directory with files"""
    temp_dir = tempfile.mkdtemp()
    
    # Create test files
    (Path(temp_dir) / "file1.txt").write_text("Content 1")
    (Path(temp_dir) / "file2.txt").write_text("Content 2")
    
    assert os.path.exists(os.path.join(temp_dir, "file1.txt"))
    assert os.path.exists(os.path.join(temp_dir, "file2.txt"))
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    assert not os.path.exists(temp_dir)


@patch('cos.commands.ls.ConfigManager')
@patch('cos.commands.ls.COSAuthenticator')
@patch('cos.commands.ls.COSClient')
def test_ls_command_import(mock_client, mock_auth, mock_config):
    """Test that ls command can be imported and mocked"""
    # Setup mocks
    mock_config_instance = Mock()
    mock_config_instance.get_output_format = Mock(return_value="table")
    mock_config.return_value = mock_config_instance
    
    mock_auth_instance = Mock()
    mock_auth_instance.authenticate = Mock(return_value=Mock())
    mock_auth.return_value = mock_auth_instance
    
    mock_client_instance = Mock()
    mock_client_instance.list_buckets = Mock(return_value=[])
    mock_client.return_value = mock_client_instance
    
    # Just verify we can call the function
    assert callable(ls)


@patch('cos.commands.cp.ConfigManager')
@patch('cos.commands.cp.COSAuthenticator')
def test_cp_command_import(mock_auth, mock_config):
    """Test that cp command can be imported"""
    assert callable(cp)


@patch('cos.commands.mv.ConfigManager')
def test_mv_command_import(mock_config):
    """Test that mv command can be imported"""
    assert callable(mv)


@patch('cos.commands.rm.ConfigManager')
def test_rm_command_import(mock_config):
    """Test that rm command can be imported"""
    assert callable(rm)


@patch('cos.commands.presign.ConfigManager')
def test_presign_command_import(mock_config):
    """Test that presign command can be imported"""
    assert callable(presign)


@patch('cos.commands.sync.ConfigManager')
def test_sync_command_import(mock_config):
    """Test that sync command can be imported"""
    assert callable(sync)


def test_cos_uri_parsing():
    """Test COS URI parsing logic"""
    from cos.utils import parse_cos_uri, is_cos_uri
    
    assert is_cos_uri("cos://bucket/key")
    assert is_cos_uri("cos://bucket/")
    assert not is_cos_uri("/local/path")
    assert not is_cos_uri("http://example.com")
    
    bucket, key = parse_cos_uri("cos://test-bucket/path/to/file.txt")
    assert bucket == "test-bucket"
    assert key == "path/to/file.txt"


def test_file_size_formatting():
    """Test file size formatting"""
    from cos.utils import format_size
    
    assert format_size(0) == "0.0 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1024 * 1024) == "1.0 MB"
    assert format_size(1024 * 1024 * 1024) == "1.0 GB"


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print("="*60)
    print("COS CLI Commands Test Suite")
    print("="*60)
    print()
    
    result = TestResult()
    
    # Run all tests
    tests = [
        test_mock_cos_client_creation,
        test_mock_list_objects,
        test_temp_file_creation,
        test_temp_dir_with_files,
        test_ls_command_import,
        test_cp_command_import,
        test_mv_command_import,
        test_rm_command_import,
        test_presign_command_import,
        test_sync_command_import,
        test_cos_uri_parsing,
        test_file_size_formatting,
    ]
    
    for test in tests:
        run_test(test, result)
    
    success = result.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

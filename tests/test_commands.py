"""Comprehensive tests for COS CLI commands: cp, ls, mv, presign, rm, sync"""

import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from datetime import datetime

from cos.commands.ls import ls
from cos.commands.cp import cp
from cos.commands.mv import mv
from cos.commands.rm import rm
from cos.commands.presign import presign
from cos.commands.sync import sync


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def cli_runner():
    """Create Click CLI test runner"""
    return CliRunner()


@pytest.fixture
def mock_cos_client():
    """Mock COS client"""
    client = Mock()
    client.list_buckets = Mock(return_value=[
        {"Name": "test-bucket-1", "Location": "ap-shanghai", "CreationDate": "2024-01-01T00:00:00.000Z"},
        {"Name": "test-bucket-2", "Location": "ap-beijing", "CreationDate": "2024-01-02T00:00:00.000Z"},
    ])
    client.list_objects = Mock(return_value={
        "Contents": [
            {"Key": "file1.txt", "Size": 1024, "LastModified": "2024-01-01T12:00:00.000Z"},
            {"Key": "file2.txt", "Size": 2048, "LastModified": "2024-01-02T12:00:00.000Z"},
        ],
        "CommonPrefixes": [
            {"Prefix": "folder1/"},
            {"Prefix": "folder2/"},
        ]
    })
    client.upload_file = Mock(return_value={"ETag": "test-etag"})
    client.download_file = Mock(return_value={"ETag": "test-etag"})
    client.delete_object = Mock(return_value={})
    client.copy_object = Mock(return_value={"ETag": "test-etag"})
    return client


@pytest.fixture
def mock_cos_s3_client():
    """Mock raw COS S3 client"""
    client = Mock()
    client.get_presigned_url = Mock(return_value="https://test-bucket.cos.ap-shanghai.myqcloud.com/test.txt?sign=xxx")
    client.list_objects = Mock(return_value={
        "Contents": [
            {"Key": "file1.txt", "Size": "1024", "LastModified": "2024-01-01T12:00:00.000Z"},
        ]
    })
    return client


@pytest.fixture
def mock_authenticator(mock_cos_s3_client):
    """Mock authenticator"""
    auth = Mock()
    auth.authenticate = Mock(return_value=mock_cos_s3_client)
    return auth


@pytest.fixture
def mock_config_manager():
    """Mock configuration manager"""
    config = Mock()
    config.get_output_format = Mock(return_value="table")
    config.get_config_value = Mock(side_effect=lambda k, d=None: {
        "region": "ap-shanghai",
        "bucket": "test-bucket",
        "prefix": ""
    }.get(k, d))
    return config


@pytest.fixture
def temp_test_file():
    """Create temporary test file"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test content\n")
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_test_dir():
    """Create temporary test directory with files"""
    temp_dir = tempfile.mkdtemp()
    
    # Create test files
    (Path(temp_dir) / "file1.txt").write_text("Content 1")
    (Path(temp_dir) / "file2.txt").write_text("Content 2")
    (Path(temp_dir) / "subdir").mkdir()
    (Path(temp_dir) / "subdir" / "file3.txt").write_text("Content 3")
    
    yield temp_dir
    
    # Cleanup
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


# ============================================================================
# LS COMMAND TESTS
# ============================================================================

class TestLsCommand:
    """Tests for ls command"""
    
    @patch('cos.commands.ls.ConfigManager')
    @patch('cos.commands.ls.COSAuthenticator')
    @patch('cos.commands.ls.COSClient')
    def test_ls_list_buckets(self, mock_client_class, mock_auth_class, 
                            mock_config_class, cli_runner, mock_cos_client,
                            mock_authenticator, mock_config_manager):
        """Test listing all buckets"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        result = cli_runner.invoke(ls, [], obj={"profile": "default"})
        
        assert result.exit_code == 0
        mock_cos_client.list_buckets.assert_called_once()
    
    @patch('cos.commands.ls.ConfigManager')
    @patch('cos.commands.ls.COSAuthenticator')
    @patch('cos.commands.ls.COSClient')
    def test_ls_list_objects(self, mock_client_class, mock_auth_class,
                            mock_config_class, cli_runner, mock_cos_client,
                            mock_authenticator, mock_config_manager):
        """Test listing objects in bucket"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        result = cli_runner.invoke(ls, ['cos://test-bucket/'], obj={"profile": "default"})
        
        assert result.exit_code == 0
        mock_cos_client.list_objects.assert_called_once()
    
    @patch('cos.commands.ls.ConfigManager')
    @patch('cos.commands.ls.COSAuthenticator')
    @patch('cos.commands.ls.COSClient')
    def test_ls_recursive(self, mock_client_class, mock_auth_class,
                         mock_config_class, cli_runner, mock_cos_client,
                         mock_authenticator, mock_config_manager):
        """Test recursive listing"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        result = cli_runner.invoke(ls, ['cos://test-bucket/', '-r'], obj={"profile": "default"})
        
        assert result.exit_code == 0
        # Verify delimiter is empty for recursive
        call_args = mock_cos_client.list_objects.call_args
        assert call_args[1]['delimiter'] == ""
    
    @patch('cos.commands.ls.ConfigManager')
    @patch('cos.commands.ls.COSAuthenticator')
    @patch('cos.commands.ls.COSClient')
    def test_ls_with_prefix(self, mock_client_class, mock_auth_class,
                           mock_config_class, cli_runner, mock_cos_client,
                           mock_authenticator, mock_config_manager):
        """Test listing with prefix"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        result = cli_runner.invoke(ls, ['cos://test-bucket/data/'], obj={"profile": "default"})
        
        assert result.exit_code == 0
        call_args = mock_cos_client.list_objects.call_args
        assert call_args[1]['prefix'] == "data/"


# ============================================================================
# CP COMMAND TESTS
# ============================================================================

class TestCpCommand:
    """Tests for cp command"""
    
    @patch('cos.commands.cp.ConfigManager')
    @patch('cos.commands.cp.COSAuthenticator')
    @patch('cos.commands.cp.COSClient')
    def test_cp_upload_file(self, mock_client_class, mock_auth_class,
                           mock_config_class, cli_runner, mock_cos_client,
                           mock_authenticator, mock_config_manager, temp_test_file):
        """Test uploading a file to COS"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        result = cli_runner.invoke(cp, [
            temp_test_file,
            'cos://test-bucket/test.txt',
            '--no-progress'
        ], obj={"profile": "default"})
        
        assert result.exit_code == 0
        mock_cos_client.upload_file.assert_called()
    
    @patch('cos.commands.cp.ConfigManager')
    @patch('cos.commands.cp.COSAuthenticator')
    @patch('cos.commands.cp.COSClient')
    def test_cp_download_file(self, mock_client_class, mock_auth_class,
                             mock_config_class, cli_runner, mock_cos_client,
                             mock_authenticator, mock_config_manager):
        """Test downloading a file from COS"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_path = os.path.join(temp_dir, "downloaded.txt")
            
            result = cli_runner.invoke(cp, [
                'cos://test-bucket/test.txt',
                dest_path,
                '--no-progress'
            ], obj={"profile": "default"})
            
            assert result.exit_code == 0
            mock_cos_client.download_file.assert_called()
    
    @patch('cos.commands.cp.ConfigManager')
    @patch('cos.commands.cp.COSAuthenticator')
    @patch('cos.commands.cp.COSClient')
    def test_cp_between_buckets(self, mock_client_class, mock_auth_class,
                                mock_config_class, cli_runner, mock_cos_client,
                                mock_authenticator, mock_config_manager):
        """Test copying between COS buckets"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        result = cli_runner.invoke(cp, [
            'cos://bucket1/file.txt',
            'cos://bucket2/file.txt',
            '--no-progress'
        ], obj={"profile": "default"})
        
        assert result.exit_code == 0
        mock_cos_client.copy_object.assert_called()
    
    @patch('cos.commands.cp.ConfigManager')
    @patch('cos.commands.cp.COSAuthenticator')
    @patch('cos.commands.cp.COSClient')
    def test_cp_recursive(self, mock_client_class, mock_auth_class,
                         mock_config_class, cli_runner, mock_cos_client,
                         mock_authenticator, mock_config_manager, temp_test_dir):
        """Test recursive copy"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        result = cli_runner.invoke(cp, [
            temp_test_dir,
            'cos://test-bucket/dir/',
            '-r',
            '--no-progress'
        ], obj={"profile": "default"})
        
        # Should upload multiple files
        assert mock_cos_client.upload_file.call_count >= 3


# ============================================================================
# MV COMMAND TESTS
# ============================================================================

class TestMvCommand:
    """Tests for mv command"""
    
    @patch('cos.commands.mv.ConfigManager')
    @patch('cos.commands.mv.COSAuthenticator')
    @patch('cos.commands.mv.COSClient')
    def test_mv_within_cos(self, mock_client_class, mock_auth_class,
                          mock_config_class, cli_runner, mock_cos_client,
                          mock_authenticator, mock_config_manager):
        """Test moving file within COS"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        result = cli_runner.invoke(mv, [
            'cos://test-bucket/old.txt',
            'cos://test-bucket/new.txt',
            '--no-progress'
        ], obj={"profile": "default"})
        
        assert result.exit_code == 0
        # Move = Copy + Delete
        mock_cos_client.copy_object.assert_called()
        mock_cos_client.delete_object.assert_called()
    
    @patch('cos.commands.mv.ConfigManager')
    @patch('cos.commands.mv.COSAuthenticator')
    @patch('cos.commands.mv.COSClient')
    def test_mv_upload_and_delete_local(self, mock_client_class, mock_auth_class,
                                       mock_config_class, cli_runner, mock_cos_client,
                                       mock_authenticator, mock_config_manager,
                                       temp_test_file):
        """Test moving local file to COS (upload and delete local)"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        result = cli_runner.invoke(mv, [
            temp_test_file,
            'cos://test-bucket/test.txt',
            '--no-progress'
        ], obj={"profile": "default"})
        
        assert result.exit_code == 0
        mock_cos_client.upload_file.assert_called()

    @patch('cos.commands.mv.ConfigManager')
    @patch('cos.commands.mv.COSAuthenticator')
    @patch('cos.commands.mv.COSClient')
    def test_mv_with_flags_parse(self, mock_client_class, mock_auth_class,
                                 mock_config_class, cli_runner, mock_cos_client,
                                 mock_authenticator, mock_config_manager,
                                 temp_test_file):
        """Test mv accepts part-size/retry flags and still uploads (no-progress)"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client

        result = cli_runner.invoke(mv, [
            temp_test_file,
            'cos://test-bucket/test.txt',
            '--no-progress', '--part-size', '1MB', '--max-retries', '2', '--retry-backoff', '0.1', '--retry-backoff-max', '0.5'
        ], obj={"profile": "default"})

        assert result.exit_code == 0
        mock_cos_client.upload_file.assert_called()


# ============================================================================
# RM COMMAND TESTS
# ============================================================================

class TestRmCommand:
    """Tests for rm command"""
    
    @patch('cos.commands.rm.ConfigManager')
    @patch('cos.commands.rm.COSAuthenticator')
    @patch('cos.commands.rm.COSClient')
    def test_rm_single_file(self, mock_client_class, mock_auth_class,
                           mock_config_class, cli_runner, mock_cos_client,
                           mock_authenticator, mock_config_manager):
        """Test deleting single file"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        result = cli_runner.invoke(rm, [
            'cos://test-bucket/test.txt'
        ], obj={"profile": "default"})
        
        assert result.exit_code == 0
        mock_cos_client.delete_object.assert_called_once()
    
    @patch('cos.commands.rm.ConfigManager')
    @patch('cos.commands.rm.COSAuthenticator')
    @patch('cos.commands.rm.COSClient')
    def test_rm_recursive(self, mock_client_class, mock_auth_class,
                         mock_config_class, cli_runner, mock_cos_client,
                         mock_authenticator, mock_config_manager):
        """Test recursive deletion"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        # Mock list_objects to return multiple files
        mock_cos_client.list_objects.return_value = {
            "Contents": [
                {"Key": "dir/file1.txt"},
                {"Key": "dir/file2.txt"},
            ]
        }
        
        result = cli_runner.invoke(rm, [
            'cos://test-bucket/dir/',
            '-r'
        ], obj={"profile": "default"})
        
        assert result.exit_code == 0
        # Should delete multiple files
        assert mock_cos_client.delete_object.call_count >= 2
    
    @patch('cos.commands.rm.ConfigManager')
    @patch('cos.commands.rm.COSAuthenticator')
    @patch('cos.commands.rm.COSClient')
    def test_rm_with_force(self, mock_client_class, mock_auth_class,
                          mock_config_class, cli_runner, mock_cos_client,
                          mock_authenticator, mock_config_manager):
        """Test deletion with force flag (no confirmation)"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        result = cli_runner.invoke(rm, [
            'cos://test-bucket/test.txt',
            '--force'
        ], obj={"profile": "default"})
        
        assert result.exit_code == 0
        mock_cos_client.delete_object.assert_called()


# ============================================================================
# PRESIGN COMMAND TESTS
# ============================================================================

class TestPresignCommand:
    """Tests for presign command"""
    
    @patch('cos.commands.presign.ConfigManager')
    @patch('cos.commands.presign.COSAuthenticator')
    def test_presign_get_url(self, mock_auth_class, mock_config_class,
                            cli_runner, mock_cos_s3_client,
                            mock_authenticator, mock_config_manager):
        """Test generating GET presigned URL"""
        mock_config_class.return_value = mock_config_manager
        mock_authenticator.authenticate.return_value = mock_cos_s3_client
        mock_auth_class.return_value = mock_authenticator
        
        result = cli_runner.invoke(presign, [
            'cos://test-bucket/test.txt'
        ], obj={"profile": "default"})
        
        assert result.exit_code == 0
        assert "https://" in result.output
        mock_cos_s3_client.get_presigned_url.assert_called_once()
    
    @patch('cos.commands.presign.ConfigManager')
    @patch('cos.commands.presign.COSAuthenticator')
    def test_presign_with_expiration(self, mock_auth_class, mock_config_class,
                                     cli_runner, mock_cos_s3_client,
                                     mock_authenticator, mock_config_manager):
        """Test generating presigned URL with custom expiration"""
        mock_config_class.return_value = mock_config_manager
        mock_authenticator.authenticate.return_value = mock_cos_s3_client
        mock_auth_class.return_value = mock_authenticator
        
        result = cli_runner.invoke(presign, [
            'cos://test-bucket/test.txt',
            '--expires-in', '7200'
        ], obj={"profile": "default"})
        
        assert result.exit_code == 0
        call_args = mock_cos_s3_client.get_presigned_url.call_args
        assert call_args[1]['Expired'] == 7200
    
    @patch('cos.commands.presign.ConfigManager')
    @patch('cos.commands.presign.COSAuthenticator')
    def test_presign_put_method(self, mock_auth_class, mock_config_class,
                               cli_runner, mock_cos_s3_client,
                               mock_authenticator, mock_config_manager):
        """Test generating PUT presigned URL"""
        mock_config_class.return_value = mock_config_manager
        mock_authenticator.authenticate.return_value = mock_cos_s3_client
        mock_auth_class.return_value = mock_authenticator
        
        result = cli_runner.invoke(presign, [
            'cos://test-bucket/test.txt',
            '--method', 'PUT'
        ], obj={"profile": "default"})
        
        assert result.exit_code == 0
        call_args = mock_cos_s3_client.get_presigned_url.call_args
        assert call_args[1]['Method'] == 'PUT'
    
    @patch('cos.commands.presign.ConfigManager')
    @patch('cos.commands.presign.COSAuthenticator')
    def test_presign_invalid_expiration(self, mock_auth_class, mock_config_class,
                                       cli_runner, mock_cos_s3_client,
                                       mock_authenticator, mock_config_manager):
        """Test presign with invalid expiration (too short)"""
        mock_config_class.return_value = mock_config_manager
        mock_authenticator.authenticate.return_value = mock_cos_s3_client
        mock_auth_class.return_value = mock_authenticator
        
        result = cli_runner.invoke(presign, [
            'cos://test-bucket/test.txt',
            '--expires-in', '30'  # Less than 60 seconds
        ], obj={"profile": "default"})
        
        assert result.exit_code != 0


# ============================================================================
# SYNC COMMAND TESTS
# ============================================================================

class TestSyncCommand:
    """Tests for sync command"""
    
    @patch('cos.commands.sync.ConfigManager')
    @patch('cos.commands.sync.COSAuthenticator')
    @patch('cos.commands.sync.COSClient')
    def test_sync_upload(self, mock_client_class, mock_auth_class,
                        mock_config_class, cli_runner, mock_cos_client,
                        mock_authenticator, mock_config_manager, temp_test_dir):
        """Test syncing local directory to COS"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        # Mock that remote doesn't have these files
        mock_cos_client.list_objects.return_value = {"Contents": []}
        
        result = cli_runner.invoke(sync, [
            temp_test_dir,
            'cos://test-bucket/sync/',
            '--no-progress'
        ], obj={"profile": "default"})
        
        assert result.exit_code == 0
        # Should upload files
        assert mock_cos_client.upload_file.call_count >= 1
    
    @patch('cos.commands.sync.ConfigManager')
    @patch('cos.commands.sync.COSAuthenticator')
    @patch('cos.commands.sync.COSClient')
    def test_sync_download(self, mock_client_class, mock_auth_class,
                          mock_config_class, cli_runner, mock_cos_client,
                          mock_authenticator, mock_config_manager):
        """Test syncing COS to local directory"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        # Mock remote files
        mock_cos_client.list_objects.return_value = {
            "Contents": [
                {"Key": "file1.txt", "Size": 1024},
                {"Key": "file2.txt", "Size": 2048},
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = cli_runner.invoke(sync, [
                'cos://test-bucket/sync/',
                temp_dir,
                '--no-progress'
            ], obj={"profile": "default"})
            
            assert result.exit_code == 0
            # Should download files
            assert mock_cos_client.download_file.call_count >= 1
    
    @patch('cos.commands.sync.ConfigManager')
    @patch('cos.commands.sync.COSAuthenticator')
    @patch('cos.commands.sync.COSClient')
    def test_sync_with_delete(self, mock_client_class, mock_auth_class,
                             mock_config_class, cli_runner, mock_cos_client,
                             mock_authenticator, mock_config_manager, temp_test_dir):
        """Test sync with --delete flag"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        # Mock remote has extra files
        mock_cos_client.list_objects.return_value = {
            "Contents": [
                {"Key": "extra.txt", "Size": 1024},
            ]
        }
        
        result = cli_runner.invoke(sync, [
            temp_test_dir,
            'cos://test-bucket/sync/',
            '--delete',
            '--no-progress'
        ], obj={"profile": "default"})
        
        assert result.exit_code == 0
        # Should delete extra remote files
        mock_cos_client.delete_object.assert_called()
    
    @patch('cos.commands.sync.ConfigManager')
    @patch('cos.commands.sync.COSAuthenticator')
    @patch('cos.commands.sync.COSClient')
    def test_sync_with_exclude(self, mock_client_class, mock_auth_class,
                              mock_config_class, cli_runner, mock_cos_client,
                              mock_authenticator, mock_config_manager, temp_test_dir):
        """Test sync with exclude pattern"""
        mock_config_class.return_value = mock_config_manager
        mock_auth_class.return_value = mock_authenticator
        mock_client_class.return_value = mock_cos_client
        
        mock_cos_client.list_objects.return_value = {"Contents": []}
        
        result = cli_runner.invoke(sync, [
            temp_test_dir,
            'cos://test-bucket/sync/',
            '--exclude', '*.txt',
            '--no-progress'
        ], obj={"profile": "default"})
        
        assert result.exit_code == 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestCommandIntegration:
    """Integration tests for command combinations"""
    
    def test_cp_then_ls(self, cli_runner, mock_cos_client, mock_authenticator, 
                       mock_config_manager, temp_test_file):
        """Test copy followed by listing"""
        # This would be a real integration test with actual COS
        # For now, just verify commands can be called in sequence
        pass
    
    def test_sync_then_rm(self, cli_runner, mock_cos_client, mock_authenticator,
                         mock_config_manager, temp_test_dir):
        """Test sync followed by deletion"""
        # This would be a real integration test with actual COS
        pass

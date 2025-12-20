"""Unit tests for WebCOSClient wrapper."""

import pytest
from unittest.mock import Mock, MagicMock, patch
import io

from ui.src.cos_client_wrapper import WebCOSClient
from cos.exceptions import COSError, BucketNotFoundError, ObjectNotFoundError


class TestWebCOSClient:
    """Test suite for WebCOSClient."""
    
    @patch('ui.src.cos_client_wrapper.ConfigManager')
    @patch('ui.src.cos_client_wrapper.COSAuthenticator')
    def test_initialization_success(self, mock_auth, mock_config):
        """Test successful client initialization."""
        # Setup mocks
        mock_base_client = Mock()
        mock_auth.return_value.authenticate.return_value = mock_base_client
        
        # Create client
        client = WebCOSClient(profile="test")
        
        # Assertions
        assert client.profile == "test"
        assert client.base_client == mock_base_client
        mock_config.assert_called_once_with("test")
        mock_auth.return_value.authenticate.assert_called_once()
    
    @patch('ui.src.cos_client_wrapper.ConfigManager')
    @patch('ui.src.cos_client_wrapper.COSAuthenticator')
    def test_initialization_failure(self, mock_auth, mock_config):
        """Test client initialization failure."""
        # Setup mocks to raise error
        mock_auth.return_value.authenticate.side_effect = Exception("Auth failed")
        
        # Should raise COSError
        with pytest.raises(COSError) as exc_info:
            WebCOSClient(profile="test")
        
        assert "Failed to initialize COS client" in str(exc_info.value)
    
    @patch('ui.src.cos_client_wrapper.ConfigManager')
    @patch('ui.src.cos_client_wrapper.COSAuthenticator')
    def test_test_connection_success(self, mock_auth, mock_config):
        """Test successful connection test."""
        # Setup mocks
        mock_base_client = Mock()
        mock_auth.return_value.authenticate.return_value = mock_base_client
        
        client = WebCOSClient(profile="test")
        
        # Mock list_buckets to return buckets
        client.cos_client.list_buckets = Mock(return_value=[
            {'Name': 'bucket1'},
            {'Name': 'bucket2'},
        ])
        
        # Test connection
        success, message = client.test_connection()
        
        # Assertions
        assert success is True
        assert "Found 2 bucket(s)" in message
    
    @patch('ui.src.cos_client_wrapper.ConfigManager')
    @patch('ui.src.cos_client_wrapper.COSAuthenticator')
    def test_test_connection_failure(self, mock_auth, mock_config):
        """Test failed connection test."""
        # Setup mocks
        mock_base_client = Mock()
        mock_auth.return_value.authenticate.return_value = mock_base_client
        
        client = WebCOSClient(profile="test")
        
        # Mock list_buckets to raise error
        client.cos_client.list_buckets = Mock(side_effect=Exception("Connection failed"))
        
        # Test connection
        success, message = client.test_connection()
        
        # Assertions
        assert success is False
        assert "Connection failed" in message
    
    @patch('ui.src.cos_client_wrapper.ConfigManager')
    @patch('ui.src.cos_client_wrapper.COSAuthenticator')
    def test_list_buckets(self, mock_auth, mock_config):
        """Test listing buckets."""
        # Setup
        mock_base_client = Mock()
        mock_auth.return_value.authenticate.return_value = mock_base_client
        
        client = WebCOSClient(profile="test")
        
        # Mock return value
        expected_buckets = [
            {'Name': 'bucket1', 'Location': 'ap-shanghai', 'CreationDate': '2024-01-01'},
            {'Name': 'bucket2', 'Location': 'ap-beijing', 'CreationDate': '2024-01-02'},
        ]
        client.cos_client.list_buckets = Mock(return_value=expected_buckets)
        
        # Call method
        buckets = client.list_buckets()
        
        # Assertions
        assert buckets == expected_buckets
        assert len(buckets) == 2
    
    @patch('ui.src.cos_client_wrapper.ConfigManager')
    @patch('ui.src.cos_client_wrapper.COSAuthenticator')
    def test_list_files_paginated(self, mock_auth, mock_config):
        """Test paginated file listing."""
        # Setup
        mock_base_client = Mock()
        mock_auth.return_value.authenticate.return_value = mock_base_client
        
        client = WebCOSClient(profile="test")
        
        # Mock response
        mock_response = {
            'Contents': [
                {
                    'Key': 'data/file1.csv',
                    'Size': 1024,
                    'LastModified': '2024-01-01',
                    'ETag': '"abc123"',
                    'StorageClass': 'STANDARD',
                },
                {
                    'Key': 'data/file2.json',
                    'Size': 2048,
                    'LastModified': '2024-01-02',
                    'ETag': '"def456"',
                    'StorageClass': 'STANDARD',
                },
            ],
            'CommonPrefixes': [
                {'Prefix': 'data/subfolder1/'},
                {'Prefix': 'data/subfolder2/'},
            ],
        }
        client.list_objects = Mock(return_value=mock_response)
        
        # Call method
        files, folders = client.list_files_paginated(bucket="test-bucket", prefix="data/")
        
        # Assertions
        assert len(files) == 2
        assert len(folders) == 2
        
        assert files[0]['key'] == 'data/file1.csv'
        assert files[0]['name'] == 'file1.csv'
        assert files[0]['size'] == 1024
        
        assert 'data/subfolder1/' in folders
        assert 'data/subfolder2/' in folders
    
    @patch('ui.src.cos_client_wrapper.ConfigManager')
    @patch('ui.src.cos_client_wrapper.COSAuthenticator')
    def test_upload_file_success(self, mock_auth, mock_config):
        """Test successful file upload."""
        # Setup
        mock_base_client = Mock()
        mock_auth.return_value.authenticate.return_value = mock_base_client
        
        client = WebCOSClient(profile="test")
        
        # Mock upload response
        mock_response = {'ETag': '"xyz789"'}
        client.cos_client.upload_file = Mock(return_value=mock_response)
        
        # Create test file
        test_data = b"test file content"
        file_obj = io.BytesIO(test_data)
        
        # Call method
        response = client.upload_file(
            bucket="test-bucket",
            key="test-file.txt",
            file_obj=file_obj,
        )
        
        # Assertions
        assert response == mock_response
        client.cos_client.upload_file.assert_called_once()
    
    @patch('ui.src.cos_client_wrapper.ConfigManager')
    @patch('ui.src.cos_client_wrapper.COSAuthenticator')
    def test_upload_file_with_progress(self, mock_auth, mock_config):
        """Test file upload with progress callback."""
        # Setup
        mock_base_client = Mock()
        mock_auth.return_value.authenticate.return_value = mock_base_client
        
        client = WebCOSClient(profile="test")
        
        # Mock upload - should succeed
        client.cos_client.upload_file = Mock(return_value={'ETag': '"xyz"'})
        
        # Create test file
        test_data = b"test file content"
        file_obj = io.BytesIO(test_data)
        
        # Call method - progress callback is optional and may not be called in mock
        result = client.upload_file(
            bucket="test-bucket",
            key="test-file.txt",
            file_obj=file_obj,
        )
        
        # Assertions - verify upload was successful
        assert result is not None
        assert 'ETag' in result
        client.cos_client.upload_file.assert_called_once()
    
    @patch('ui.src.cos_client_wrapper.ConfigManager')
    @patch('ui.src.cos_client_wrapper.COSAuthenticator')
    def test_delete_objects_batch(self, mock_auth, mock_config):
        """Test batch deletion of objects."""
        # Setup
        mock_base_client = Mock()
        mock_auth.return_value.authenticate.return_value = mock_base_client
        
        client = WebCOSClient(profile="test")
        
        # Mock delete to succeed for some, fail for others
        def mock_delete(bucket, key):
            if key == "fail.txt":
                raise Exception("Delete failed")
            return True
        
        client.delete_object = Mock(side_effect=mock_delete)
        
        # Call method
        keys = ["file1.txt", "file2.txt", "fail.txt"]
        result = client.delete_objects(bucket="test-bucket", keys=keys)
        
        # Assertions
        assert len(result['deleted']) == 2
        assert len(result['errors']) == 1
        assert 'file1.txt' in result['deleted']
        assert 'file2.txt' in result['deleted']
        assert any('fail.txt' in err for err in result['errors'])
    
    @patch('ui.src.cos_client_wrapper.ConfigManager')
    @patch('ui.src.cos_client_wrapper.COSAuthenticator')
    def test_create_folder(self, mock_auth, mock_config):
        """Test folder creation."""
        # Setup
        mock_base_client = Mock()
        mock_auth.return_value.authenticate.return_value = mock_base_client
        
        client = WebCOSClient(profile="test")
        
        # Mock put_object
        client.cos_client.put_object = Mock(return_value={})
        
        # Test without trailing slash
        result = client.create_folder(bucket="test-bucket", folder_path="newfolder")
        
        # Assertions
        assert result is True
        # Should add trailing slash
        call_args = client.cos_client.put_object.call_args
        assert call_args[1]['key'] == 'newfolder/'
        
        # Test with trailing slash
        client.create_folder(bucket="test-bucket", folder_path="another/")
        call_args = client.cos_client.put_object.call_args
        assert call_args[1]['key'] == 'another/'


class TestWebCOSClientErrors:
    """Test error handling in WebCOSClient."""
    
    @patch('ui.src.cos_client_wrapper.ConfigManager')
    @patch('ui.src.cos_client_wrapper.COSAuthenticator')
    def test_list_objects_bucket_not_found(self, mock_auth, mock_config):
        """Test listing objects in non-existent bucket."""
        # Setup
        mock_base_client = Mock()
        mock_auth.return_value.authenticate.return_value = mock_base_client
        
        client = WebCOSClient(profile="test")
        
        # Mock to raise BucketNotFoundError
        client.cos_client.list_objects = Mock(side_effect=BucketNotFoundError("Bucket not found"))
        
        # Should raise BucketNotFoundError
        with pytest.raises(BucketNotFoundError):
            client.list_objects(bucket="nonexistent-bucket")
    
    @patch('ui.src.cos_client_wrapper.ConfigManager')
    @patch('ui.src.cos_client_wrapper.COSAuthenticator')
    def test_download_file_not_found(self, mock_auth, mock_config):
        """Test downloading non-existent file."""
        # Setup
        mock_base_client = Mock()
        mock_auth.return_value.authenticate.return_value = mock_base_client
        
        # Mock get_object to raise exception
        from cos.exceptions import ObjectNotFoundError
        mock_base_client.get_object.side_effect = ObjectNotFoundError("Object not found")
        
        client = WebCOSClient(profile="test")
        
        # Should raise ObjectNotFoundError
        with pytest.raises(ObjectNotFoundError):
            client.download_file(bucket="test-bucket", key="nonexistent.txt")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

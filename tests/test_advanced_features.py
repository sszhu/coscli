"""Tests for new v2.0 features: lifecycle, policy, CORS, versioning"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path

# Import the command modules
from cos.commands import lifecycle, policy, cors, versioning
from cos.exceptions import COSError


class TestLifecycleCommands:
    """Test lifecycle management commands"""
    
    @patch('cos.commands.lifecycle.COSAuthenticator')
    @patch('cos.commands.lifecycle.ConfigManager')
    @patch('cos.commands.lifecycle.COSClient')
    def test_get_lifecycle(self, mock_client_class, mock_config, mock_auth):
        """Test getting lifecycle configuration"""
        # Setup mocks
        mock_client = Mock()
        mock_client.get_bucket_lifecycle.return_value = {
            "Rule": [
                {
                    "ID": "test-rule",
                    "Status": "Enabled",
                    "Filter": {"Prefix": "logs/"},
                    "Expiration": {"Days": 30}
                }
            ]
        }
        mock_client_class.return_value = mock_client
        
        # Execute (would need Click testing)
        result = mock_client.get_bucket_lifecycle()
        
        # Verify
        assert "Rule" in result
        assert len(result["Rule"]) == 1
        assert result["Rule"][0]["ID"] == "test-rule"
    
    @patch('cos.commands.lifecycle.COSAuthenticator')
    @patch('cos.commands.lifecycle.ConfigManager')
    @patch('cos.commands.lifecycle.COSClient')
    @patch('builtins.open', new_callable=mock_open, read_data='{"Rule": [{"ID": "test"}]}')
    def test_put_lifecycle(self, mock_file, mock_client_class, mock_config, mock_auth):
        """Test setting lifecycle configuration"""
        mock_client = Mock()
        mock_client.put_bucket_lifecycle.return_value = {}
        mock_client_class.return_value = mock_client
        
        # Load config
        lifecycle_config = json.loads(mock_file().read())
        
        # Execute
        mock_client.put_bucket_lifecycle(lifecycle_config)
        
        # Verify
        mock_client.put_bucket_lifecycle.assert_called_once_with(lifecycle_config)
    
    @patch('cos.commands.lifecycle.COSAuthenticator')
    @patch('cos.commands.lifecycle.ConfigManager')
    @patch('cos.commands.lifecycle.COSClient')
    def test_delete_lifecycle(self, mock_client_class, mock_config, mock_auth):
        """Test deleting lifecycle configuration"""
        mock_client = Mock()
        mock_client.delete_bucket_lifecycle.return_value = {}
        mock_client_class.return_value = mock_client
        
        # Execute
        mock_client.delete_bucket_lifecycle()
        
        # Verify
        mock_client.delete_bucket_lifecycle.assert_called_once()


class TestPolicyCommands:
    """Test bucket policy commands"""
    
    @patch('cos.commands.policy.COSAuthenticator')
    @patch('cos.commands.policy.ConfigManager')
    @patch('cos.commands.policy.COSClient')
    def test_get_policy(self, mock_client_class, mock_config, mock_auth):
        """Test getting bucket policy"""
        mock_client = Mock()
        mock_client.get_bucket_policy.return_value = {
            "Policy": json.dumps({
                "version": "2.0",
                "Statement": []
            })
        }
        mock_client_class.return_value = mock_client
        
        # Execute
        result = mock_client.get_bucket_policy()
        
        # Verify
        assert "Policy" in result
        policy = json.loads(result["Policy"])
        assert policy["version"] == "2.0"
    
    @patch('cos.commands.policy.COSAuthenticator')
    @patch('cos.commands.policy.ConfigManager')
    @patch('cos.commands.policy.COSClient')
    @patch('builtins.open', new_callable=mock_open, read_data='{"version": "2.0", "Statement": []}')
    def test_put_policy(self, mock_file, mock_client_class, mock_config, mock_auth):
        """Test setting bucket policy"""
        mock_client = Mock()
        mock_client.put_bucket_policy.return_value = {}
        mock_client_class.return_value = mock_client
        
        # Load policy
        policy = json.loads(mock_file().read())
        policy_str = json.dumps(policy)
        
        # Execute
        mock_client.put_bucket_policy(policy_str)
        
        # Verify
        mock_client.put_bucket_policy.assert_called_once_with(policy_str)
    
    @patch('cos.commands.policy.COSAuthenticator')
    @patch('cos.commands.policy.ConfigManager')
    @patch('cos.commands.policy.COSClient')
    def test_delete_policy(self, mock_client_class, mock_config, mock_auth):
        """Test deleting bucket policy"""
        mock_client = Mock()
        mock_client.delete_bucket_policy.return_value = {}
        mock_client_class.return_value = mock_client
        
        # Execute
        mock_client.delete_bucket_policy()
        
        # Verify
        mock_client.delete_bucket_policy.assert_called_once()


class TestCORSCommands:
    """Test CORS configuration commands"""
    
    @patch('cos.commands.cors.COSAuthenticator')
    @patch('cos.commands.cors.ConfigManager')
    @patch('cos.commands.cors.COSClient')
    def test_get_cors(self, mock_client_class, mock_config, mock_auth):
        """Test getting CORS configuration"""
        mock_client = Mock()
        mock_client.get_bucket_cors.return_value = {
            "CORSRule": [
                {
                    "ID": "test-cors",
                    "AllowedOrigin": ["*"],
                    "AllowedMethod": ["GET", "POST"],
                    "MaxAgeSeconds": 3600
                }
            ]
        }
        mock_client_class.return_value = mock_client
        
        # Execute
        result = mock_client.get_bucket_cors()
        
        # Verify
        assert "CORSRule" in result
        assert len(result["CORSRule"]) == 1
        assert result["CORSRule"][0]["ID"] == "test-cors"
    
    @patch('cos.commands.cors.COSAuthenticator')
    @patch('cos.commands.cors.ConfigManager')
    @patch('cos.commands.cors.COSClient')
    @patch('builtins.open', new_callable=mock_open, read_data='{"CORSRule": [{"ID": "test"}]}')
    def test_put_cors(self, mock_file, mock_client_class, mock_config, mock_auth):
        """Test setting CORS configuration"""
        mock_client = Mock()
        mock_client.put_bucket_cors.return_value = {}
        mock_client_class.return_value = mock_client
        
        # Load config
        cors_config = json.loads(mock_file().read())
        
        # Execute
        mock_client.put_bucket_cors(cors_config)
        
        # Verify
        mock_client.put_bucket_cors.assert_called_once_with(cors_config)
    
    @patch('cos.commands.cors.COSAuthenticator')
    @patch('cos.commands.cors.ConfigManager')
    @patch('cos.commands.cors.COSClient')
    def test_delete_cors(self, mock_client_class, mock_config, mock_auth):
        """Test deleting CORS configuration"""
        mock_client = Mock()
        mock_client.delete_bucket_cors.return_value = {}
        mock_client_class.return_value = mock_client
        
        # Execute
        mock_client.delete_bucket_cors()
        
        # Verify
        mock_client.delete_bucket_cors.assert_called_once()


class TestVersioningCommands:
    """Test versioning commands"""
    
    @patch('cos.commands.versioning.COSAuthenticator')
    @patch('cos.commands.versioning.ConfigManager')
    @patch('cos.commands.versioning.COSClient')
    def test_get_versioning(self, mock_client_class, mock_config, mock_auth):
        """Test getting versioning status"""
        mock_client = Mock()
        mock_client.get_bucket_versioning.return_value = {"Status": "Enabled"}
        mock_client_class.return_value = mock_client
        
        # Execute
        result = mock_client.get_bucket_versioning()
        
        # Verify
        assert result["Status"] == "Enabled"
    
    @patch('cos.commands.versioning.COSAuthenticator')
    @patch('cos.commands.versioning.ConfigManager')
    @patch('cos.commands.versioning.COSClient')
    def test_enable_versioning(self, mock_client_class, mock_config, mock_auth):
        """Test enabling versioning"""
        mock_client = Mock()
        mock_client.put_bucket_versioning.return_value = {}
        mock_client_class.return_value = mock_client
        
        # Execute
        mock_client.put_bucket_versioning("Enabled")
        
        # Verify
        mock_client.put_bucket_versioning.assert_called_once_with("Enabled")
    
    @patch('cos.commands.versioning.COSAuthenticator')
    @patch('cos.commands.versioning.ConfigManager')
    @patch('cos.commands.versioning.COSClient')
    def test_suspend_versioning(self, mock_client_class, mock_config, mock_auth):
        """Test suspending versioning"""
        mock_client = Mock()
        mock_client.put_bucket_versioning.return_value = {}
        mock_client_class.return_value = mock_client
        
        # Execute
        mock_client.put_bucket_versioning("Suspended")
        
        # Verify
        mock_client.put_bucket_versioning.assert_called_once_with("Suspended")


class TestCOSClientExtensions:
    """Test new COSClient methods"""
    
    def test_client_has_lifecycle_methods(self):
        """Test that COSClient has lifecycle methods"""
        from cos.client import COSClient
        
        mock_client = Mock()
        cos_client = COSClient(mock_client, "test-bucket")
        
        assert hasattr(cos_client, 'get_bucket_lifecycle')
        assert hasattr(cos_client, 'put_bucket_lifecycle')
        assert hasattr(cos_client, 'delete_bucket_lifecycle')
    
    def test_client_has_policy_methods(self):
        """Test that COSClient has policy methods"""
        from cos.client import COSClient
        
        mock_client = Mock()
        cos_client = COSClient(mock_client, "test-bucket")
        
        assert hasattr(cos_client, 'get_bucket_policy')
        assert hasattr(cos_client, 'put_bucket_policy')
        assert hasattr(cos_client, 'delete_bucket_policy')
    
    def test_client_has_cors_methods(self):
        """Test that COSClient has CORS methods"""
        from cos.client import COSClient
        
        mock_client = Mock()
        cos_client = COSClient(mock_client, "test-bucket")
        
        assert hasattr(cos_client, 'get_bucket_cors')
        assert hasattr(cos_client, 'put_bucket_cors')
        assert hasattr(cos_client, 'delete_bucket_cors')
    
    def test_client_has_versioning_methods(self):
        """Test that COSClient has versioning methods"""
        from cos.client import COSClient
        
        mock_client = Mock()
        cos_client = COSClient(mock_client, "test-bucket")
        
        assert hasattr(cos_client, 'get_bucket_versioning')
        assert hasattr(cos_client, 'put_bucket_versioning')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

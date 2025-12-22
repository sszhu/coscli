"""Tests for token command and STS functionality"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from click.testing import CliRunner

from cos.commands.token import token, build_policy, extract_appid_from_bucket
from cos.auth import STSTokenManager


class TestBuildPolicy:
    """Test policy building functionality"""
    
    def test_build_policy_with_prefix(self):
        """Test building policy with prefix restriction"""
        policy = build_policy(
            bucket="mybucket-1234567890",
            region="ap-shanghai",
            appid="1234567890",
            prefix="data/uploads"
        )
        
        assert policy["version"] == "2.0"
        assert len(policy["statement"]) == 2
        
        # Check resource constraint
        resource = policy["statement"][0]["resource"][0]
        assert "data/uploads/" in resource
        assert resource.endswith("*")
        assert "ap-shanghai" in resource
        assert "1234567890" in resource
        
        # Check actions
        actions = policy["statement"][0]["action"]
        assert "name/cos:GetObject" in actions
        assert "name/cos:PutObject" in actions
        assert "name/cos:DeleteObject" in actions
    
    def test_build_policy_read_only(self):
        """Test building read-only policy"""
        policy = build_policy(
            bucket="mybucket-1234567890",
            region="ap-shanghai",
            appid="1234567890",
            prefix="reports",
            read_only=True
        )
        
        actions = policy["statement"][0]["action"]
        assert "name/cos:GetObject" in actions
        assert "name/cos:HeadObject" in actions
        # Should not have write actions
        assert "name/cos:PutObject" not in actions
        assert "name/cos:DeleteObject" not in actions
    
    def test_build_policy_without_prefix(self):
        """Test building policy without prefix (full bucket access)"""
        policy = build_policy(
            bucket="mybucket-1234567890",
            region="ap-shanghai",
            appid="1234567890"
        )
        
        resource = policy["statement"][0]["resource"][0]
        assert resource.endswith("mybucket-1234567890/*")
        # Should not have prefix-specific path
        assert "mybucket-1234567890//" not in resource
    
    def test_build_policy_custom_actions(self):
        """Test building policy with custom actions"""
        custom_actions = ["GetObject", "PutObject"]
        policy = build_policy(
            bucket="mybucket-1234567890",
            region="ap-shanghai",
            appid="1234567890",
            actions=custom_actions
        )
        
        actions = policy["statement"][0]["action"]
        assert len(actions) == 2
        assert "name/cos:GetObject" in actions
        assert "name/cos:PutObject" in actions
    
    def test_build_policy_prefix_with_trailing_slash(self):
        """Test that trailing slash in prefix is handled correctly"""
        policy1 = build_policy(
            bucket="mybucket-1234567890",
            region="ap-shanghai",
            appid="1234567890",
            prefix="data/uploads/"
        )
        
        policy2 = build_policy(
            bucket="mybucket-1234567890",
            region="ap-shanghai",
            appid="1234567890",
            prefix="data/uploads"
        )
        
        # Both should produce the same resource
        assert policy1["statement"][0]["resource"] == policy2["statement"][0]["resource"]
    
    def test_build_policy_bucket_level_operations(self):
        """Test that bucket-level operations are included"""
        policy = build_policy(
            bucket="mybucket-1234567890",
            region="ap-shanghai",
            appid="1234567890",
            prefix="data"
        )
        
        # Second statement should have bucket operations
        assert len(policy["statement"]) == 2
        bucket_statement = policy["statement"][1]
        assert "name/cos:HeadBucket" in bucket_statement["action"]
        assert "name/cos:GetBucket" in bucket_statement["action"]
        
        # Should NOT have prefix condition (allows listing entire bucket)
        # The actual object access is restricted by the resource path
        assert "condition" not in bucket_statement


class TestExtractAppidFromBucket:
    """Test APPID extraction from bucket name"""
    
    def test_extract_appid_valid(self):
        """Test extracting APPID from valid bucket name"""
        appid = extract_appid_from_bucket("mybucket-1234567890")
        assert appid == "1234567890"
    
    def test_extract_appid_multiple_hyphens(self):
        """Test extraction with multiple hyphens in name"""
        appid = extract_appid_from_bucket("my-test-bucket-1234567890")
        assert appid == "1234567890"
    
    def test_extract_appid_invalid_no_appid(self):
        """Test extraction fails for bucket without APPID"""
        appid = extract_appid_from_bucket("mybucket")
        assert appid is None
    
    def test_extract_appid_invalid_short_number(self):
        """Test extraction fails for short number suffix"""
        appid = extract_appid_from_bucket("mybucket-123")
        assert appid is None
    
    def test_extract_appid_invalid_non_numeric(self):
        """Test extraction fails for non-numeric suffix"""
        appid = extract_appid_from_bucket("mybucket-abcdefghij")
        assert appid is None


class TestTokenCommand:
    """Test token command CLI"""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    @pytest.fixture
    def mock_config(self):
        with patch('cos.commands.token.ConfigManager') as mock:
            config = mock.return_value
            config.get_credentials.return_value = {
                "secret_id": "test_id",
                "secret_key": "test_key",
                "assume_role": "qcs::cam::uin/123:roleName/test-role"
            }
            config.get_region.return_value = "ap-shanghai"
            config.get_output_format.return_value = "table"
            yield mock
    
    @pytest.fixture
    def mock_sts(self):
        with patch('cos.commands.token.STSTokenManager') as mock:
            sts = mock.return_value
            sts.get_temp_credentials.return_value = {
                "tmp_secret_id": "TEMP_ID_123",
                "tmp_secret_key": "TEMP_KEY_456",
                "token": "TOKEN_789"
            }
            yield mock
    
    def test_token_basic(self, runner, mock_config, mock_sts):
        """Test basic token generation"""
        result = runner.invoke(token, ['--duration', '3600'], obj={})
        
        assert result.exit_code == 0
        assert "TEMP_ID_123" in result.output or "..." in result.output
    
    def test_token_no_assume_role(self, runner):
        """Test token generation fails without assume_role"""
        with patch('cos.commands.token.ConfigManager') as mock_config:
            config = mock_config.return_value
            config.get_credentials.return_value = {
                "secret_id": "test_id",
                "secret_key": "test_key"
                # No assume_role
            }
            
            result = runner.invoke(token, obj={})
            
            assert result.exit_code == 1
            assert "Assume role ARN is required" in result.output
    
    def test_token_with_bucket_and_prefix(self, runner, mock_config, mock_sts):
        """Test token generation with bucket and prefix"""
        result = runner.invoke(
            token,
            [
                '--bucket', 'mybucket-1234567890',
                '--prefix', 'data/uploads',
                '--duration', '3600'
            ],
            obj={}
        )
        
        assert result.exit_code == 0
        
        # Verify policy was built and passed
        sts_instance = mock_sts.return_value
        sts_instance.get_temp_credentials.assert_called_once()
        call_args = sts_instance.get_temp_credentials.call_args
        assert 'policy' in call_args.kwargs
        policy = call_args.kwargs['policy']
        assert policy is not None
        assert "data/uploads/" in str(policy)
    
    def test_token_read_only(self, runner, mock_config, mock_sts):
        """Test read-only token generation"""
        result = runner.invoke(
            token,
            [
                '--bucket', 'mybucket-1234567890',
                '--prefix', 'reports',
                '--read-only',
                '--duration', '3600'
            ],
            obj={}
        )
        
        assert result.exit_code == 0
        
        # Verify read-only policy
        sts_instance = mock_sts.return_value
        call_args = sts_instance.get_temp_credentials.call_args
        policy = call_args.kwargs['policy']
        actions = policy["statement"][0]["action"]
        assert "name/cos:GetObject" in actions
        assert "name/cos:PutObject" not in actions
    
    def test_token_env_output(self, runner, mock_config, mock_sts):
        """Test token generation with env output format"""
        result = runner.invoke(
            token,
            ['--output', 'env', '--duration', '3600'],
            obj={}
        )
        
        assert result.exit_code == 0
        assert "export COS_SECRET_ID=" in result.output
        assert "export COS_SECRET_KEY=" in result.output
        assert "export COS_TOKEN=" in result.output
        assert "TEMP_ID_123" in result.output
    
    def test_token_json_output(self, runner, mock_config, mock_sts):
        """Test token generation with JSON output format"""
        result = runner.invoke(
            token,
            ['--output', 'json', '--duration', '3600'],
            obj={}
        )
        
        assert result.exit_code == 0
        # Should contain JSON structure
        assert "Credentials" in result.output or "tmp_secret_id" in result.output
    
    def test_token_duration_validation(self, runner, mock_config):
        """Test token duration validation"""
        # Too short
        result = runner.invoke(token, ['--duration', '600'], obj={})
        assert result.exit_code == 1
        assert "at least 900 seconds" in result.output
        
        # Too long
        result = runner.invoke(token, ['--duration', '50000'], obj={})
        assert result.exit_code == 1
        assert "cannot exceed 43200 seconds" in result.output
    
    def test_token_bucket_without_appid(self, runner, mock_config):
        """Test token generation fails for bucket without valid APPID"""
        result = runner.invoke(
            token,
            ['--bucket', 'invalidbucket', '--prefix', 'data'],
            obj={}
        )
        
        assert result.exit_code == 1
        assert "APPID" in result.output
    
    def test_token_cos_uri_bucket(self, runner, mock_config, mock_sts):
        """Test token generation with cos:// URI as bucket"""
        result = runner.invoke(
            token,
            ['--bucket', 'cos://mybucket-1234567890/data/uploads'],
            obj={}
        )
        
        assert result.exit_code == 0
        
        # Should parse bucket and prefix from URI
        sts_instance = mock_sts.return_value
        call_args = sts_instance.get_temp_credentials.call_args
        policy = call_args.kwargs['policy']
        assert "mybucket-1234567890" in str(policy)
        assert "data/uploads" in str(policy)
    
    def test_token_custom_actions(self, runner, mock_config, mock_sts):
        """Test token generation with custom actions"""
        result = runner.invoke(
            token,
            [
                '--bucket', 'mybucket-1234567890',
                '--action', 'GetObject',
                '--action', 'PutObject'
            ],
            obj={}
        )
        
        assert result.exit_code == 0
        
        # Verify custom actions in policy
        sts_instance = mock_sts.return_value
        call_args = sts_instance.get_temp_credentials.call_args
        policy = call_args.kwargs['policy']
        actions = policy["statement"][0]["action"]
        assert "name/cos:GetObject" in actions
        assert "name/cos:PutObject" in actions
        assert len(actions) == 2


class TestSTSTokenManager:
    """Test STSTokenManager class"""
    
    def test_init(self):
        """Test STSTokenManager initialization"""
        manager = STSTokenManager(
            secret_id="test_id",
            secret_key="test_key",
            assume_role="test_role"
        )
        
        assert manager.secret_id == "test_id"
        assert manager.secret_key == "test_key"
        assert manager.assume_role == "test_role"
        assert manager.sts_duration == 7200  # Default
    
    @patch('cos.auth.sts_client.StsClient')
    def test_get_temp_credentials_no_policy(self, mock_sts_client):
        """Test getting temporary credentials without policy"""
        # Mock STS response
        mock_resp = Mock()
        mock_resp.__str__ = Mock(return_value=json.dumps({
            "Credentials": {
                "TmpSecretId": "TEMP_ID",
                "TmpSecretKey": "TEMP_KEY",
                "Token": "TOKEN"
            }
        }))
        mock_client_instance = mock_sts_client.return_value
        mock_client_instance.AssumeRole.return_value = mock_resp
        
        manager = STSTokenManager(
            secret_id="test_id",
            secret_key="test_key",
            assume_role="test_role"
        )
        
        creds = manager.get_temp_credentials(region="ap-shanghai")
        
        assert creds["tmp_secret_id"] == "TEMP_ID"
        assert creds["tmp_secret_key"] == "TEMP_KEY"
        assert creds["token"] == "TOKEN"
    
    @patch('cos.auth.sts_client.StsClient')
    def test_get_temp_credentials_with_policy(self, mock_sts_client):
        """Test getting temporary credentials with policy"""
        # Mock STS response
        mock_resp = Mock()
        mock_resp.__str__ = Mock(return_value=json.dumps({
            "Credentials": {
                "TmpSecretId": "TEMP_ID",
                "TmpSecretKey": "TEMP_KEY",
                "Token": "TOKEN"
            }
        }))
        mock_client_instance = mock_sts_client.return_value
        mock_client_instance.AssumeRole.return_value = mock_resp
        
        manager = STSTokenManager(
            secret_id="test_id",
            secret_key="test_key",
            assume_role="test_role"
        )
        
        policy = {
            "version": "2.0",
            "statement": [{"effect": "allow", "action": ["name/cos:GetObject"]}]
        }
        
        creds = manager.get_temp_credentials(
            region="ap-shanghai",
            policy=policy
        )
        
        assert creds["tmp_secret_id"] == "TEMP_ID"
        # Verify policy was included in request
        mock_client_instance.AssumeRole.assert_called_once()
    
    @patch('cos.auth.sts_client.StsClient')
    def test_credentials_caching(self, mock_sts_client):
        """Test that credentials are cached"""
        # Mock STS response
        mock_resp = Mock()
        mock_resp.__str__ = Mock(return_value=json.dumps({
            "Credentials": {
                "TmpSecretId": "TEMP_ID",
                "TmpSecretKey": "TEMP_KEY",
                "Token": "TOKEN"
            }
        }))
        mock_client_instance = mock_sts_client.return_value
        mock_client_instance.AssumeRole.return_value = mock_resp
        
        manager = STSTokenManager(
            secret_id="test_id",
            secret_key="test_key",
            assume_role="test_role"
        )
        
        # First call
        creds1 = manager.get_temp_credentials(region="ap-shanghai")
        # Second call (should use cache)
        creds2 = manager.get_temp_credentials(region="ap-shanghai")
        
        # Should only call AssumeRole once
        assert mock_client_instance.AssumeRole.call_count == 1
        assert creds1 == creds2
    
    @patch('cos.auth.sts_client.StsClient')
    def test_no_cache_with_policy(self, mock_sts_client):
        """Test that credentials are not cached when policy is provided"""
        # Mock STS response
        mock_resp = Mock()
        mock_resp.__str__ = Mock(return_value=json.dumps({
            "Credentials": {
                "TmpSecretId": "TEMP_ID",
                "TmpSecretKey": "TEMP_KEY",
                "Token": "TOKEN"
            }
        }))
        mock_client_instance = mock_sts_client.return_value
        mock_client_instance.AssumeRole.return_value = mock_resp
        
        manager = STSTokenManager(
            secret_id="test_id",
            secret_key="test_key",
            assume_role="test_role"
        )
        
        policy = {"version": "2.0", "statement": []}
        
        # Two calls with policy
        creds1 = manager.get_temp_credentials(region="ap-shanghai", policy=policy)
        creds2 = manager.get_temp_credentials(region="ap-shanghai", policy=policy)
        
        # Should call AssumeRole twice (no caching with policy)
        assert mock_client_instance.AssumeRole.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

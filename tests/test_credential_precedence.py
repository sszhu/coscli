"""
Test credential precedence rules.

Tests the 4-mode credential resolution:
1. Environment temporary token (highest priority)
2. Config file temporary token
3. STS via assume_role
4. Permanent credentials (lowest priority)
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from cos.config import ConfigManager
from cos.exceptions import ConfigurationError


class TestCredentialPrecedence:
    """Test credential precedence rules using real temp config files."""

    def setup_method(self):
        """Create temp config directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        self.config_file = self.config_dir / "config"
        self.credentials_file = self.config_dir / "credentials"
    
    def teardown_method(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def write_credentials(self, content: str):
        """Write content to credentials file."""
        self.credentials_file.write_text(content)
        os.chmod(self.credentials_file, 0o600)
    
    def test_mode1_env_temp_credentials_ignore_config_assume_role(self):
        """
        Mode 1: When COS_TOKEN is set in environment, should use ONLY env vars
        and completely ignore config file (including assume_role).
        """
        # Write config file with assume_role (should be IGNORED)
        self.write_credentials("""[default]
secret_id = config_secret_id
secret_key = config_secret_key
assume_role = qcs::cam::uin/123456:roleName/ShouldBeIgnored
""")
        
        # Set environment variables
        env_vars = {
            'COS_TOKEN': 'env_token_value',
            'COS_SECRET_ID': 'env_secret_id',
            'COS_SECRET_KEY': 'env_secret_key'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('cos.config.CONFIG_DIR', self.config_dir):
                with patch('cos.config.CONFIG_FILE', self.config_file):
                    with patch('cos.config.CREDENTIALS_FILE', self.credentials_file):
                        config_manager = ConfigManager()
                        credentials = config_manager.get_credentials()
                        
                        # Should use environment credentials
                        assert credentials['secret_id'] == 'env_secret_id'
                        assert credentials['secret_key'] == 'env_secret_key'
                        assert credentials['token'] == 'env_token_value'
                        
                        # Should NOT have assume_role (even though it's in config)
                        assert 'assume_role' not in credentials
                        
                        # Should track source
                        assert credentials['_source'] == 'env_temp'

    def test_mode1_env_temp_incomplete_raises_error(self):
        """
        Mode 1: If COS_TOKEN is set but COS_SECRET_ID or COS_SECRET_KEY is missing,
        should raise clear error.
        """
        # Only set COS_TOKEN, missing secret_id and secret_key
        env_vars = {
            'COS_TOKEN': 'env_token_value'
            # Missing COS_SECRET_ID and COS_SECRET_KEY
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('cos.config.CONFIG_DIR', self.config_dir):
                with patch('cos.config.CONFIG_FILE', self.config_file):
                    with patch('cos.config.CREDENTIALS_FILE', self.credentials_file):
                        config_manager = ConfigManager()
                        
                        with pytest.raises(ConfigurationError, match="COS_TOKEN"):
                            config_manager.get_credentials()

    def test_mode2a_config_temp_token_ignores_assume_role(self):
        """
        Mode 2a: When token is in config file, should use it and ignore assume_role.
        """
        # Config file with both token and assume_role
        self.write_credentials("""[default]
secret_id = config_secret_id
secret_key = config_secret_key
token = config_token_value
assume_role = qcs::cam::uin/123456:roleName/ShouldBeIgnored
""")
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('cos.config.CONFIG_DIR', self.config_dir):
                with patch('cos.config.CONFIG_FILE', self.config_file):
                    with patch('cos.config.CREDENTIALS_FILE', self.credentials_file):
                        config_manager = ConfigManager()
                        credentials = config_manager.get_credentials()
                        
                        # Should use config temp credentials
                        assert credentials['secret_id'] == 'config_secret_id'
                        assert credentials['secret_key'] == 'config_secret_key'
                        assert credentials['token'] == 'config_token_value'
                        
                        # Should NOT have assume_role
                        assert 'assume_role' not in credentials
                        
                        # Should track source
                        assert credentials['_source'] == 'config_temp'

    def test_mode2b_config_assume_role_when_no_token(self):
        """
        Mode 2b: When assume_role is in config but no token, should include assume_role.
        """
        # Config file with assume_role but no token
        self.write_credentials("""[default]
secret_id = config_secret_id
secret_key = config_secret_key
assume_role = qcs::cam::uin/123456:roleName/MyRole
""")
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('cos.config.CONFIG_DIR', self.config_dir):
                with patch('cos.config.CONFIG_FILE', self.config_file):
                    with patch('cos.config.CREDENTIALS_FILE', self.credentials_file):
                        config_manager = ConfigManager()
                        credentials = config_manager.get_credentials()
                        
                        # Should include base credentials
                        assert credentials['secret_id'] == 'config_secret_id'
                        assert credentials['secret_key'] == 'config_secret_key'
                        
                        # Should include assume_role
                        assert credentials['assume_role'] == 'qcs::cam::uin/123456:roleName/MyRole'
                        
                        # Should NOT have token
                        assert 'token' not in credentials
                        
                        # Should track source
                        assert credentials['_source'] == 'sts'

    def test_mode3_permanent_credentials(self):
        """
        Mode 3: When no token or assume_role, should return permanent credentials.
        """
        # Config file with only permanent credentials
        self.write_credentials("""[default]
secret_id = config_secret_id
secret_key = config_secret_key
""")
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('cos.config.CONFIG_DIR', self.config_dir):
                with patch('cos.config.CONFIG_FILE', self.config_file):
                    with patch('cos.config.CREDENTIALS_FILE', self.credentials_file):
                        config_manager = ConfigManager()
                        credentials = config_manager.get_credentials()
                        
                        # Should have permanent credentials
                        assert credentials['secret_id'] == 'config_secret_id'
                        assert credentials['secret_key'] == 'config_secret_key'
                        
                        # Should NOT have token or assume_role
                        assert 'token' not in credentials
                        assert 'assume_role' not in credentials
                        
                        # Should track source
                        assert credentials['_source'] == 'permanent'

    def test_env_overrides_config_permanent_credentials(self):
        """
        Mode 3 variant: Environment permanent credentials override config file.
        """
        # Config file with different permanent credentials
        self.write_credentials("""[default]
secret_id = config_secret_id
secret_key = config_secret_key
""")
        
        # Environment with permanent credentials (no token)
        env_vars = {
            'COS_SECRET_ID': 'env_secret_id',
            'COS_SECRET_KEY': 'env_secret_key'
            # No COS_TOKEN
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('cos.config.CONFIG_DIR', self.config_dir):
                with patch('cos.config.CONFIG_FILE', self.config_file):
                    with patch('cos.config.CREDENTIALS_FILE', self.credentials_file):
                        config_manager = ConfigManager()
                        credentials = config_manager.get_credentials()
                        
                        # Should use environment credentials (env overrides config)
                        assert credentials['secret_id'] == 'env_secret_id'
                        assert credentials['secret_key'] == 'env_secret_key'
                        
                        # Should track source as permanent (no token)
                        assert credentials['_source'] == 'permanent'

    def test_env_secret_with_config_assume_role(self):
        """
        Scenario: Environment has permanent credentials, config has assume_role.
        Should use env credentials to assume the role.
        """
        # Config file with assume_role
        self.write_credentials("""[default]
secret_id = config_secret_id
secret_key = config_secret_key
assume_role = qcs::cam::uin/123456:roleName/MyRole
""")
        
        # Environment with permanent credentials (no token)
        env_vars = {
            'COS_SECRET_ID': 'env_secret_id',
            'COS_SECRET_KEY': 'env_secret_key'
            # No COS_TOKEN
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('cos.config.CONFIG_DIR', self.config_dir):
                with patch('cos.config.CONFIG_FILE', self.config_file):
                    with patch('cos.config.CREDENTIALS_FILE', self.credentials_file):
                        config_manager = ConfigManager()
                        credentials = config_manager.get_credentials()
                        
                        # Should use environment credentials (override config)
                        assert credentials['secret_id'] == 'env_secret_id'
                        assert credentials['secret_key'] == 'env_secret_key'
                        
                        # Should include assume_role from config
                        assert credentials['assume_role'] == 'qcs::cam::uin/123456:roleName/MyRole'
                        
                        # Should track source as STS
                        assert credentials['_source'] == 'sts'

    def test_has_env_credentials_helper(self):
        """Test has_env_credentials() helper method."""
        with patch('cos.config.CONFIG_DIR', self.config_dir):
            with patch('cos.config.CONFIG_FILE', self.config_file):
                with patch('cos.config.CREDENTIALS_FILE', self.credentials_file):
                    config_manager = ConfigManager()
                    
                    # Test 1: No env credentials
                    with patch.dict(os.environ, {}, clear=True):
                        assert config_manager.has_env_credentials() is False
                    
                    # Test 2: Only COS_TOKEN (incomplete)
                    with patch.dict(os.environ, {'COS_TOKEN': 'value'}, clear=True):
                        assert config_manager.has_env_credentials() is True  # Has token
                    
                    # Test 3: Complete temp credentials
                    with patch.dict(os.environ, {
                        'COS_TOKEN': 'value',
                        'COS_SECRET_ID': 'id',
                        'COS_SECRET_KEY': 'key'
                    }, clear=True):
                        assert config_manager.has_env_credentials() is True
                    
                    # Test 4: Only permanent credentials (no token) - this WILL return True
                    # because has_env_credentials checks for ANY credential env var
                    with patch.dict(os.environ, {
                        'COS_SECRET_ID': 'id',
                        'COS_SECRET_KEY': 'key'
                    }, clear=True):
                        assert config_manager.has_env_credentials() is True  # Has secret_id/secret_key


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

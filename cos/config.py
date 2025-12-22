"""Configuration management for COS CLI"""

import os
from configparser import ConfigParser
from pathlib import Path
from typing import Any, Dict, Optional

from .constants import (
    CONFIG_DIR,
    CONFIG_FILE,
    CREDENTIALS_FILE,
    DEFAULT_PROFILE,
    DEFAULT_REGION,
    DEFAULT_OUTPUT,
    ENV_SECRET_ID,
    ENV_SECRET_KEY,
    ENV_REGION,
    ENV_ASSUME_ROLE,
    ENV_OUTPUT,
    ENV_PROFILE,
    ENV_ENDPOINT_URL,
)
from .exceptions import ConfigurationError
from .utils import ensure_directory


class ConfigManager:
    """Manages configuration and credentials"""
    
    def __init__(self, profile: str = DEFAULT_PROFILE):
        """
        Initialize configuration manager.
        
        Args:
            profile: Profile name to use
        """
        self.profile = profile
        self.config_dir = CONFIG_DIR
        self.config_file = CONFIG_FILE
        self.credentials_file = CREDENTIALS_FILE
        
        # Ensure config directory exists
        ensure_directory(self.config_dir)
        
        # Load configurations
        self.config = self._load_config()
        self.credentials = self._load_credentials()
    
    def _load_config(self) -> ConfigParser:
        """Load configuration from file"""
        config = ConfigParser()
        if self.config_file.exists():
            config.read(self.config_file)
        return config
    
    def _load_credentials(self) -> ConfigParser:
        """Load credentials from file"""
        credentials = ConfigParser()
        if self.credentials_file.exists():
            credentials.read(self.credentials_file)
            # Set proper permissions
            os.chmod(self.credentials_file, 0o600)
        return credentials
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        with open(self.config_file, "w") as f:
            self.config.write(f)
    
    def _save_credentials(self) -> None:
        """Save credentials to file"""
        with open(self.credentials_file, "w") as f:
            self.credentials.write(f)
        # Set proper permissions
        os.chmod(self.credentials_file, 0o600)
    
    def get_profile_section(self) -> str:
        """Get profile section name"""
        if self.profile == DEFAULT_PROFILE:
            return DEFAULT_PROFILE
        return f"profile {self.profile}"
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Priority: Environment variable > Config file > Default
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        # Check environment variables
        env_var = f"COS_{key.upper()}"
        if env_var in os.environ:
            return os.environ[env_var]
        
        # Check config file
        section = self.get_profile_section()
        if self.config.has_section(section) and self.config.has_option(section, key):
            return self.config.get(section, key)
        
        return default
    
    def set_config_value(self, key: str, value: str) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        section = self.get_profile_section()
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        self._save_config()
    
    def get_credential_value(self, key: str) -> Optional[str]:
        """
        Get credential value.
        
        Priority: Environment variable > Credentials file
        
        Args:
            key: Credential key
            
        Returns:
            Credential value or None
        """
        # Check environment variables
        env_var = f"COS_{key.upper()}"
        if env_var in os.environ:
            return os.environ[env_var]
        
        # Check credentials file
        section = self.get_profile_section()
        if self.credentials.has_section(section) and self.credentials.has_option(section, key):
            return self.credentials.get(section, key)
        
        return None
    
    def has_env_credentials(self) -> bool:
        """
        Check if any credential is set via environment variables.
        
        Returns:
            True if any credential environment variable is set
        """
        env_keys = ["COS_SECRET_ID", "COS_SECRET_KEY", "COS_TOKEN"]
        return any(key in os.environ for key in env_keys)
    
    def set_credential_value(self, key: str, value: str) -> None:
        """
        Set credential value.
        
        Args:
            key: Credential key
            value: Credential value
        """
        section = self.get_profile_section()
        if not self.credentials.has_section(section):
            self.credentials.add_section(section)
        self.credentials.set(section, key, value)
        self._save_credentials()
    
    def get_region(self) -> str:
        """Get region"""
        return self.get_config_value("region", DEFAULT_REGION)
    
    def get_output_format(self) -> str:
        """Get output format"""
        return self.get_config_value("output", DEFAULT_OUTPUT)
    
    def get_endpoint_url(self) -> Optional[str]:
        """Get endpoint URL"""
        return self.get_config_value("endpoint_url")
    
    def get_bucket(self) -> Optional[str]:
        """Get default bucket"""
        return self.get_config_value("bucket")
    
    def get_prefix(self) -> Optional[str]:
        """Get default prefix"""
        return self.get_config_value("prefix")
    
    def get_credentials(self) -> Dict[str, str]:
        """
        Get all credentials with clear precedence rules.
        
        Credential Resolution Precedence:
        1. If COS_TOKEN is set (environment): Use temp credentials from env
           - Requires: COS_SECRET_ID, COS_SECRET_KEY, COS_TOKEN
           - Ignores: Config file assume_role (prevents conflict)
        2. If assume_role in config: Use STS to generate temp credentials
        3. Otherwise: Use permanent credentials from config/env
        
        Returns:
            Dictionary containing credentials
            
        Raises:
            ConfigurationError: If required credentials are missing or conflict
        """
        # Check if temporary token is provided via environment
        env_token = os.environ.get("COS_TOKEN")
        
        if env_token:
            # Mode 1: Using temporary credentials from environment
            # In this mode, we ONLY use environment variables and ignore config file
            secret_id = os.environ.get("COS_SECRET_ID")
            secret_key = os.environ.get("COS_SECRET_KEY")
            
            if not secret_id or not secret_key:
                raise ConfigurationError(
                    "COS_TOKEN is set but COS_SECRET_ID or COS_SECRET_KEY is missing. "
                    "Temporary credentials require all three environment variables."
                )
            
            return {
                "secret_id": secret_id,
                "secret_key": secret_key,
                "token": env_token,
                "_source": "env_temp"
            }
        
        # Mode 2 & 3: Using config file credentials (with optional env override)
        secret_id = self.get_credential_value("secret_id")
        secret_key = self.get_credential_value("secret_key")
        
        if not secret_id or not secret_key:
            raise ConfigurationError(
                "Credentials not found. Run 'cos configure' to set them up."
            )
        
        credentials = {
            "secret_id": secret_id,
            "secret_key": secret_key,
        }
        
        # Check for token in config file (from import-token command)
        config_token = self.get_credential_value("token")
        if config_token:
            # Mode 2a: Temporary token stored in config file
            credentials["token"] = config_token
            credentials["_source"] = "config_temp"
            return credentials
        
        # Check for assume_role (STS mode)
        assume_role = self.get_credential_value("assume_role")
        if assume_role:
            # Mode 2b: Use STS to generate temporary credentials
            credentials["assume_role"] = assume_role
            credentials["_source"] = "sts"
        else:
            # Mode 3: Permanent credentials
            credentials["_source"] = "permanent"
        
        return credentials
    
    def list_all_config(self) -> Dict[str, Any]:
        """
        List all configuration values.
        
        Returns:
            Dictionary of all configuration values
        """
        section = self.get_profile_section()
        result = {}
        
        if self.config.has_section(section):
            result.update(dict(self.config.items(section)))
        
        # Add credential keys (but not values)
        if self.credentials.has_section(section):
            for key in self.credentials.options(section):
                result[key] = "****" if key in ["secret_id", "secret_key", "token"] else self.credentials.get(section, key)
        
        return result
    
    def profile_exists(self) -> bool:
        """Check if profile exists"""
        section = self.get_profile_section()
        return self.config.has_section(section) or self.credentials.has_section(section)

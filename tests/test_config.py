"""Tests for configuration management"""

import pytest
from pathlib import Path
from cos.config import ConfigManager
from cos.exceptions import ConfigurationError


def test_config_manager_init(temp_config_dir, monkeypatch):
    """Test ConfigManager initialization"""
    monkeypatch.setattr("cos.config.CONFIG_DIR", temp_config_dir)
    monkeypatch.setattr("cos.config.CONFIG_FILE", temp_config_dir / "config")
    monkeypatch.setattr("cos.config.CREDENTIALS_FILE", temp_config_dir / "credentials")
    
    config_manager = ConfigManager()
    assert config_manager.profile == "default"
    assert temp_config_dir.exists()


def test_set_get_config_value(temp_config_dir, monkeypatch):
    """Test setting and getting configuration values"""
    monkeypatch.setattr("cos.config.CONFIG_DIR", temp_config_dir)
    monkeypatch.setattr("cos.config.CONFIG_FILE", temp_config_dir / "config")
    monkeypatch.setattr("cos.config.CREDENTIALS_FILE", temp_config_dir / "credentials")
    
    config_manager = ConfigManager()
    config_manager.set_config_value("region", "ap-beijing")
    
    assert config_manager.get_config_value("region") == "ap-beijing"


def test_set_get_credential_value(temp_config_dir, monkeypatch):
    """Test setting and getting credential values"""
    monkeypatch.setattr("cos.config.CONFIG_DIR", temp_config_dir)
    monkeypatch.setattr("cos.config.CONFIG_FILE", temp_config_dir / "config")
    monkeypatch.setattr("cos.config.CREDENTIALS_FILE", temp_config_dir / "credentials")
    
    config_manager = ConfigManager()
    config_manager.set_credential_value("secret_id", "AKID_TEST")
    config_manager.set_credential_value("secret_key", "TEST_KEY")
    
    assert config_manager.get_credential_value("secret_id") == "AKID_TEST"
    assert config_manager.get_credential_value("secret_key") == "TEST_KEY"


def test_get_credentials_missing(temp_config_dir, monkeypatch):
    """Test getting credentials when they're missing"""
    monkeypatch.setattr("cos.config.CONFIG_DIR", temp_config_dir)
    monkeypatch.setattr("cos.config.CONFIG_FILE", temp_config_dir / "config")
    monkeypatch.setattr("cos.config.CREDENTIALS_FILE", temp_config_dir / "credentials")
    
    config_manager = ConfigManager()
    
    with pytest.raises(ConfigurationError):
        config_manager.get_credentials()


def test_multiple_profiles(temp_config_dir, monkeypatch):
    """Test multiple profile support"""
    monkeypatch.setattr("cos.config.CONFIG_DIR", temp_config_dir)
    monkeypatch.setattr("cos.config.CONFIG_FILE", temp_config_dir / "config")
    monkeypatch.setattr("cos.config.CREDENTIALS_FILE", temp_config_dir / "credentials")
    
    # Default profile
    config_default = ConfigManager("default")
    config_default.set_config_value("region", "ap-shanghai")
    
    # Production profile
    config_prod = ConfigManager("production")
    config_prod.set_config_value("region", "ap-beijing")
    
    assert config_default.get_config_value("region") == "ap-shanghai"
    assert config_prod.get_config_value("region") == "ap-beijing"

"""Test configuration for pytest"""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_config_dir():
    """Create temporary configuration directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_credentials():
    """Mock credentials for testing"""
    return {
        "secret_id": "AKID_TEST_123456",
        "secret_key": "TEST_SECRET_KEY_123456",
        "assume_role": "qcs::cam::uin/100000000:roleName/TestRole",
    }


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "region": "ap-shanghai",
        "output": "json",
        "endpoint_url": None,
    }

"""Tests for utility functions"""

import pytest
from cos.utils import (
    parse_cos_uri,
    format_size,
    is_cos_uri,
    join_cos_path,
)
from cos.exceptions import InvalidURIError


def test_parse_cos_uri_valid():
    """Test parsing valid COS URIs"""
    bucket, key = parse_cos_uri("cos://my-bucket/path/to/file.txt")
    assert bucket == "my-bucket"
    assert key == "path/to/file.txt"


def test_parse_cos_uri_no_key():
    """Test parsing COS URI without key"""
    bucket, key = parse_cos_uri("cos://my-bucket/")
    assert bucket == "my-bucket"
    assert key == ""


def test_parse_cos_uri_invalid():
    """Test parsing invalid COS URI"""
    with pytest.raises(InvalidURIError):
        parse_cos_uri("s3://my-bucket/file.txt")


def test_parse_cos_uri_empty_bucket():
    """Test parsing COS URI with empty bucket"""
    with pytest.raises(InvalidURIError):
        parse_cos_uri("cos:///file.txt")


def test_format_size():
    """Test size formatting"""
    assert "1.0 KB" in format_size(1024)
    assert "1.0 MB" in format_size(1024 * 1024)
    assert "1.0 GB" in format_size(1024 * 1024 * 1024)


def test_is_cos_uri():
    """Test COS URI detection"""
    assert is_cos_uri("cos://bucket/file")
    assert not is_cos_uri("/local/path")
    assert not is_cos_uri("s3://bucket/file")


def test_join_cos_path():
    """Test COS path joining"""
    assert join_cos_path("path", "to", "file") == "path/to/file"
    assert join_cos_path("/path/", "/to/", "/file/") == "path/to/file"

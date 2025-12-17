"""Constants and default values for COS CLI"""

import os
from pathlib import Path

# Configuration
CONFIG_DIR = Path.home() / ".cos"
CONFIG_FILE = CONFIG_DIR / "config"
CREDENTIALS_FILE = CONFIG_DIR / "credentials"
DEFAULT_PROFILE = "default"

# Environment variables
ENV_SECRET_ID = "COS_SECRET_ID"
ENV_SECRET_KEY = "COS_SECRET_KEY"
ENV_REGION = "COS_REGION"
ENV_ASSUME_ROLE = "COS_ASSUME_ROLE"
ENV_OUTPUT = "COS_OUTPUT"
ENV_PROFILE = "COS_PROFILE"
ENV_ENDPOINT_URL = "COS_ENDPOINT_URL"

# Defaults
DEFAULT_REGION = "ap-shanghai"
DEFAULT_OUTPUT = "table"
DEFAULT_SCHEME = "https"

# Transfer settings
MULTIPART_THRESHOLD = 5 * 1024 * 1024  # 5MB
MULTIPART_CHUNKSIZE = 5 * 1024 * 1024  # 5MB
MAX_CONCURRENCY = 10
MAX_RETRIES = 3
RETRY_BACKOFF = 2

# STS settings
STS_DURATION = 7200  # 2 hours
STS_ENDPOINT = "sts.tencentcloudapi.com"

# Output formats
OUTPUT_JSON = "json"
OUTPUT_TABLE = "table"
OUTPUT_TEXT = "text"
VALID_OUTPUTS = [OUTPUT_JSON, OUTPUT_TABLE, OUTPUT_TEXT]

# COS URI scheme
COS_URI_SCHEME = "cos://"

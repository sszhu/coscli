"""Configuration settings for COS Data Manager UI."""

import os
from pathlib import Path

# ============================================================================
# PATHS
# ============================================================================

PARENT_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = PARENT_DIR / "static" / "logos" / "tencent-logo.svg"

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================

APP_TITLE = "COS Data Manager"
APP_SUBTITLE = "Modern interface for Tencent Cloud Object Storage"
APP_VERSION = "1.0.0"

# ============================================================================
# COS CONFIGURATION
# ============================================================================

def _get_cos_config_value(key: str, default: str = "") -> str:
    """Get configuration value from COS CLI config file directly."""
    try:
        from configparser import ConfigParser
        config_file = Path.home() / ".cos" / "config"
        
        if not config_file.exists():
            return default
        
        config = ConfigParser()
        config.read(config_file)
        
        profile = os.getenv("COS_PROFILE", "default")
        section = profile if profile == "default" else f"profile {profile}"
        
        if config.has_section(section) and config.has_option(section, key):
            value = config.get(section, key)
            return value if value else default
        
        return default
    except Exception:
        return default

DEFAULT_BUCKET = os.getenv("COS_DEFAULT_BUCKET") or _get_cos_config_value("bucket", "")
DEFAULT_PREFIX = os.getenv("COS_DEFAULT_PREFIX") or _get_cos_config_value("prefix", "")
DEFAULT_REGION = os.getenv("COS_DEFAULT_REGION", "ap-shanghai")
DEFAULT_PROFILE = os.getenv("COS_PROFILE", "default")

# ============================================================================
# UI CONFIGURATION
# ============================================================================

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# File Upload
MAX_UPLOAD_SIZE_MB = 5000  # 5 GB
ALLOWED_FILE_TYPES = None  # None = all types allowed
UPLOAD_CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB chunks

# File Preview
PREVIEW_MAX_SIZE_MB = 10
PREVIEW_SUPPORTED_TYPES = ['.csv', '.json', '.txt', '.md', '.log', '.yml', '.yaml']

# ============================================================================
# FILE CATEGORY PATTERNS
# ============================================================================

# Pattern matching for file categorization
FILE_CATEGORY_PATTERNS = {
    'Data': ['.csv', '.tsv', '.parquet', '.xlsx', 'data'],
    'Code': ['.py', '.sh', '.r', '.sql', 'script', 'code'],
    'Configuration': ['.json', '.toml', '.yaml', '.yml', '.conf', 'config'],
    'Documents': ['.pdf', '.doc', '.docx', '.txt', '.md', 'document'],
    'Images': ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp', 'image'],
    'Archives': ['.zip', '.tar', '.gz', '.7z', '.rar', 'backup', 'archive'],
    'Logs': ['.log', 'log', 'debug', 'error'],
    'Models': ['.pkl', '.h5', '.pt', '.pth', '.onnx', 'model'],
}

# ============================================================================
# FILE EXTENSION EMOJIS
# ============================================================================

FILE_EXTENSION_EMOJIS = {
    # Data files
    'CSV': '📊',
    'TSV': '📊',
    'XLSX': '📊',
    'PARQUET': '📈',
    
    # Code files
    'PY': '🐍',
    'R': '📜',
    'SH': '📜',
    'SQL': '🗄️',
    
    # Config files
    'JSON': '⚙️',
    'TOML': '⚙️',
    'YAML': '⚙️',
    'YML': '⚙️',
    'CONF': '⚙️',
    
    # Documents
    'TXT': '📝',
    'MD': '📝',
    'PDF': '📄',
    'DOC': '📄',
    'DOCX': '📄',
    
    # Images
    'PNG': '🖼️',
    'JPG': '🖼️',
    'JPEG': '🖼️',
    'GIF': '🎬',
    'SVG': '🎨',
    
    # Archives
    'ZIP': '📦',
    'TAR': '📦',
    'GZ': '📦',
    '7Z': '📦',
    
    # Logs
    'LOG': '📋',
    
    # Models
    'PKL': '🧠',
    'H5': '🧠',
    'PT': '🧠',
    'PTH': '🧠',
    'ONNX': '🧠',
}

# ============================================================================
# CATEGORY EMOJIS
# ============================================================================

CATEGORY_EMOJIS = {
    'Data': '📊',
    'Code': '💻',
    'Configuration': '⚙️',
    'Documents': '📄',
    'Images': '🖼️',
    'Archives': '📦',
    'Logs': '📋',
    'Models': '🧠',
    'Other': '📁',
}

# ============================================================================
# COLOR PALETTE (Tencent/COS Branding)
# ============================================================================

COLORS = {
    # Primary
    'primary': '#006EFF',
    'primary_dark': '#0052CC',
    'primary_light': '#4D9FFF',
    
    # Secondary
    'secondary': '#00C9A7',
    'warning': '#FFB84D',
    'danger': '#FF4D4F',
    'info': '#4DA6FF',
    
    # Neutrals
    'text': '#1A1A1A',
    'text_secondary': '#4A4A4A',
    'text_muted': '#8C8C8C',
    'border': '#D9D9D9',
    'background': '#F5F5F5',
    'white': '#FFFFFF',
    
    # Semantic
    'success': '#52C41A',
    'error': '#FF4D4F',
    'folder': '#FFD666',
}

# ============================================================================
# EMOJIS
# ============================================================================

FOLDER_EMOJI = '📁'
BUCKET_EMOJI = '🪣'
FILE_EMOJI = '📄'

# ============================================================================
# API SETTINGS
# ============================================================================

# Request timeouts (seconds)
TIMEOUT_LIST = 30
TIMEOUT_UPLOAD = 300
TIMEOUT_DOWNLOAD = 300

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# ============================================================================
# SESSION STATE KEYS
# ============================================================================

SESSION_KEYS = {
    'cos_client': 'cos_client',
    'current_bucket': 'current_bucket',
    'current_prefix': 'current_prefix',
    'selected_files': 'selected_files',
    'recent_uploads': 'recent_uploads',
    'recent_downloads': 'recent_downloads',
    'upload_progress': 'upload_progress',
    'filter_settings': 'filter_settings',
    'sort_settings': 'sort_settings',
}

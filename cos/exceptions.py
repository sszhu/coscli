"""Custom exceptions for COS CLI"""


class COSError(Exception):
    """Base exception for COS CLI errors"""
    pass


class AuthenticationError(COSError):
    """Raised when authentication fails"""
    pass


class ConfigurationError(COSError):
    """Raised when configuration is invalid"""
    pass


class BucketNotFoundError(COSError):
    """Raised when bucket does not exist"""
    pass


class ObjectNotFoundError(COSError):
    """Raised when object does not exist"""
    pass


class PermissionDeniedError(COSError):
    """Raised when operation is not permitted"""
    pass


class NetworkError(COSError):
    """Raised when network operation fails"""
    pass


class TransferError(COSError):
    """Raised when file transfer fails"""
    pass


class InvalidURIError(COSError):
    """Raised when COS URI is invalid"""
    pass

"""Custom exception hierarchy for S3 storage operations."""


class S3StorageError(Exception):
    """Base exception for all S3 storage operations."""


class CredentialError(S3StorageError):
    """Raised when access_key or secret_key is missing or invalid."""


class BucketNotFoundError(S3StorageError):
    """Raised when the specified bucket does not exist."""


class FileNotFoundError(S3StorageError):
    """Raised when the specified file/key does not exist in S3."""


class UploadError(S3StorageError):
    """Raised when an upload operation fails."""


class DownloadError(S3StorageError):
    """Raised when a download operation fails."""

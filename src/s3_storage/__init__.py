"""LeapGo S3 Storage - Python SDK for S3-compatible object storage."""
from s3_storage.client import S3StorageClient
from s3_storage.exceptions import (
    S3StorageError,
    CredentialError,
    BucketNotFoundError,
)

__version__ = "1.0.0"
__all__ = ["S3StorageClient", "S3StorageError", "CredentialError", "BucketNotFoundError"]

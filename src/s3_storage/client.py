"""S3StorageClient - Unified S3-compatible storage client."""

import os
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError

from s3_storage.exceptions import (
    S3StorageError,
    CredentialError,
    BucketNotFoundError,
    FileNotFoundError as S3FileNotFoundError,
    UploadError,
    DownloadError,
)

from s3_storage.utils import normalize_key, get_file_key, guess_content_type


class S3StorageClient:
    """Unified client for S3-compatible object storage (RustFS / MinIO / OSS / AWS S3)."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "us-east-1",
        bucket: Optional[str] = None,
        bucket_prefix: str = "",
        timeout: int = 30,
        connect_timeout: int = 10,
    ):
        """Initialize the S3 client.

        Args:
            endpoint:     S3 endpoint URL, e.g. http://localhost:9000
                         Reads from env var S3_ENDPOINT if not provided.
            access_key:   Access key ID. Reads from S3_ACCESS_KEY env var if not provided.
            secret_key:   Secret access key. Reads from S3_SECRET_KEY env var if not provided.
            region:       AWS region, defaults to us-east-1. Reads S3_REGION env var if not provided.
            bucket:        Default bucket name. Reads S3_BUCKET env var if not provided.
            bucket_prefix: Path prefix prepended to all keys, e.g. "dev/" — useful for
                          multi-environment isolation.
            timeout:       Per-operation timeout in seconds.
            connect_timeout: Connection timeout in seconds.
        """
        self.endpoint = endpoint or os.getenv("S3_ENDPOINT")
        self.access_key = access_key or os.getenv("S3_ACCESS_KEY")
        self.secret_key = secret_key or os.getenv("S3_SECRET_KEY")
        self.region = region or os.getenv("S3_REGION", "us-east-1")
        self.default_bucket = bucket or os.getenv("S3_BUCKET", "leapgo")
        self.bucket_prefix = bucket_prefix
        self.timeout = timeout
        self.connect_timeout = connect_timeout

        if not self.access_key or not self.secret_key:
            raise CredentialError(
                "access_key and secret_key are required. "
                "Pass them as arguments or set S3_ACCESS_KEY / S3_SECRET_KEY env vars."
            )

        self._client = self._create_client()

    def _create_client(self):
        """Create and return a boto3 S3 client."""
        config = Config(
            signature_version="s3v4",
            connect_timeout=self.connect_timeout,
            read_timeout=self.timeout,
            retries={"max_attempts": 3, "mode": "standard"},
        )
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            config=config,
        )

    def _full_key(self, key: str) -> str:
        """Return the full key after applying bucket_prefix."""
        return normalize_key(f"{self.bucket_prefix}/{key}").lstrip("/")

    # ── Bucket operations ──────────────────────────────────────────────────────

    def list_buckets(self) -> List[str]:
        """List all bucket names."""
        try:
            resp = self._client.list_buckets()
            return [b["Name"] for b in resp.get("Buckets", [])]
        except NoCredentialsError as e:
            raise CredentialError(f"Authentication failed: {e}") from e
        except ClientError as e:
            raise S3StorageError(f"Failed to list buckets: {e}") from e

    def bucket_exists(self, bucket: Optional[str] = None) -> bool:
        """Check whether a bucket exists."""
        bucket = bucket or self.default_bucket
        try:
            self._client.head_bucket(Bucket=bucket)
            return True
        except ClientError:
            return False

    # ── Upload ────────────────────────────────────────────────────────────────

    def upload_file(
        self,
        local_path: str,
        remote_key: str,
        bucket: Optional[str] = None,
        content_type: Optional[str] = None,
        extra_args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Upload a local file to S3.

        Args:
            local_path:    Path to the local file.
            remote_key:    Key under which to store the file in S3 (bucket_prefix is applied).
            bucket:        Bucket name; defaults to default_bucket.
            content_type:  MIME type; auto-detected from extension if omitted.
            extra_args:    Additional boto3 ExtraArgs (Metadata, CacheControl, etc.).

        Returns:
            {"ETag": "...", "key": "...", "bucket": "...", "size": N, "md5": "...", "url": "..."}
        """
        bucket = bucket or self.default_bucket
        key = self._full_key(remote_key)

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")

        content_type = content_type or guess_content_type(local_path)
        args = {"ContentType": content_type}
        if extra_args:
            args.update(extra_args)

        try:
            self._client.upload_file(local_path, bucket, key, ExtraArgs=args)
            file_size = os.path.getsize(local_path)
            md5 = hashlib.md5(open(local_path, "rb").read()).hexdigest()
            return {
                "key": key,
                "bucket": bucket,
                "size": file_size,
                "md5": md5,
                "url": f"{self.endpoint}/{bucket}/{key}",
            }
        except ClientError as e:
            raise UploadError(f"Upload failed [{key}]: {e}") from e

    def upload_bytes(
        self,
        data: bytes,
        remote_key: str,
        bucket: Optional[str] = None,
        content_type: str = "application/octet-stream",
    ) -> Dict[str, Any]:
        """Upload raw bytes to S3."""
        bucket = bucket or self.default_bucket
        key = self._full_key(remote_key)
        try:
            resp = self._client.put_object(
                Bucket=bucket, Key=key, Body=data, ContentType=content_type
            )
            return {
                "key": key,
                "bucket": bucket,
                "size": len(data),
                "ETag": resp.get("ETag"),
            }
        except ClientError as e:
            raise UploadError(f"Upload failed [{key}]: {e}") from e

    # ── Download ─────────────────────────────────────────────────────────────

    def download_file(
        self,
        remote_key: str,
        local_path: str,
        bucket: Optional[str] = None,
    ) -> str:
        """Download a file from S3 to local disk.

        Args:
            remote_key:  Key of the file in S3.
            local_path:  Local destination path (including filename).
            bucket:      Bucket name; defaults to default_bucket.

        Returns:
            The local_path that was written.
        """
        bucket = bucket or self.default_bucket
        key = self._full_key(remote_key)

        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            self._client.download_file(bucket, key, local_path)
            return local_path
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey"):
                raise S3FileNotFoundError(f"File not found in S3: {key}") from e
            raise DownloadError(f"Download failed [{key}]: {e}") from e

    # ── Delete ───────────────────────────────────────────────────────────────

    def delete_file(self, remote_key: str, bucket: Optional[str] = None) -> bool:
        """Delete a single file from S3."""
        bucket = bucket or self.default_bucket
        key = self._full_key(remote_key)
        try:
            self._client.delete_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            raise S3StorageError(f"Delete failed [{key}]: {e}") from e

    def delete_files(self, remote_keys: List[str], bucket: Optional[str] = None) -> int:
        """Batch delete multiple files. Returns the count of deleted files."""
        bucket = bucket or self.default_bucket
        if not remote_keys:
            return 0
        objects = [{"Key": self._full_key(k)} for k in remote_keys]
        try:
            resp = self._client.delete_objects(
                Bucket=bucket, Delete={"Objects": objects}
            )
            deleted = len(resp.get("Deleted", []))
            return deleted
        except ClientError as e:
            raise S3StorageError(f"Batch delete failed: {e}") from e

    # ── List ─────────────────────────────────────────────────────────────────

    def list_files(
        self,
        prefix: str = "",
        bucket: Optional[str] = None,
        max_keys: int = 1000,
        include_size: bool = True,
    ) -> List[Dict[str, Any]]:
        """List files in a bucket.

        Args:
            prefix:       Filter keys by this prefix.
            bucket:        Bucket name; defaults to default_bucket.
            max_keys:     Maximum number of keys to return.
            include_size: Whether to include size and last_modified in results.

        Returns:
            [{"key": "...", "size": N, "last_modified": "...", "etag": "..."}, ...]
        """
        bucket = bucket or self.default_bucket
        full_prefix = normalize_key(f"{self.bucket_prefix}/{prefix}").lstrip("/")

        try:
            resp = self._client.list_objects_v2(
                Bucket=bucket, Prefix=full_prefix, MaxKeys=max_keys
            )
            contents = resp.get("Contents", [])
            if include_size:
                return [
                    {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj.get("LastModified"),
                        "etag": obj.get("ETag", "").strip('"'),
                    }
                    for obj in contents
                ]
            else:
                return [{"key": obj["Key"]} for obj in contents]
        except ClientError as e:
            raise S3StorageError(f"List files failed: {e}") from e

    def file_exists(self, remote_key: str, bucket: Optional[str] = None) -> bool:
        """Check whether a file exists in S3."""
        bucket = bucket or self.default_bucket
        key = self._full_key(remote_key)
        try:
            self._client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    def get_file_info(self, remote_key: str, bucket: Optional[str] = None) -> Dict[str, Any]:
        """Get metadata for a file (size, MIME type, ETag, last_modified, etc.)."""
        bucket = bucket or self.default_bucket
        key = self._full_key(remote_key)
        try:
            resp = self._client.head_object(Bucket=bucket, Key=key)
            return {
                "key": key,
                "size": resp.get("ContentLength", 0),
                "content_type": resp.get("ContentType", ""),
                "last_modified": resp.get("LastModified"),
                "etag": resp.get("ETag", "").strip('"'),
                "metadata": resp.get("Metadata", {}),
            }
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey"):
                raise S3FileNotFoundError(f"File not found in S3: {key}") from e
            raise S3StorageError(f"Get file info failed [{key}]: {e}") from e

    # ── Presigned URLs ───────────────────────────────────────────────────────

    def generate_presigned_url(
        self,
        remote_key: str,
        bucket: Optional[str] = None,
        expires_in: int = 604800,  # 7 days
    ) -> str:
        """Generate a presigned URL for reading a file (temporary public access).

        Args:
            remote_key:  S3 key.
            bucket:      Bucket name; defaults to default_bucket.
            expires_in:  Validity period in seconds; defaults to 7 days.

        Returns:
            The presigned URL string.
        """
        bucket = bucket or self.default_bucket
        key = self._full_key(remote_key)
        try:
            url = self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            raise S3StorageError(f"Generate presigned URL failed [{key}]: {e}") from e

    def generate_upload_presigned_url(
        self,
        remote_key: str,
        bucket: Optional[str] = None,
        expires_in: int = 3600,  # 1 hour
        content_type: str = "application/octet-stream",
    ) -> str:
        """Generate a presigned URL for uploading a file directly from the client.

        Args:
            remote_key:    S3 key.
            bucket:        Bucket name; defaults to default_bucket.
            expires_in:   Validity period in seconds; defaults to 1 hour.
            content_type: Expected MIME type of the uploaded content.
        """
        bucket = bucket or self.default_bucket
        key = self._full_key(remote_key)
        try:
            url = self._client.generate_presigned_url(
                "put_object",
                Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            raise S3StorageError(f"Generate upload URL failed [{key}]: {e}") from e

    # ── Copy ────────────────────────────────────────────────────────────────

    def copy_file(
        self,
        src_key: str,
        dst_key: str,
        src_bucket: Optional[str] = None,
        dst_bucket: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Copy a file within S3 (same or cross bucket)."""
        src_bucket = src_bucket or self.default_bucket
        dst_bucket = dst_bucket or self.default_bucket
        src_key = self._full_key(src_key)
        dst_key = self._full_key(dst_key)
        copy_source = {"Bucket": src_bucket, "Key": src_key}
        try:
            resp = self._client.copy_object(
                Bucket=dst_bucket, Key=dst_key, CopySource=copy_source
            )
            return {"key": dst_key, "bucket": dst_bucket, "etag": resp.get("ETag")}
        except ClientError as e:
            raise S3StorageError(f"Copy failed [{src_key}] -> [{dst_key}]: {e}") from e

    # ── Sync ────────────────────────────────────────────────────────────────

    def sync_upload(
        self,
        local_dir: str,
        remote_prefix: str = "",
        bucket: Optional[str] = None,
        pattern: str = "**/*",
    ) -> Dict[str, Any]:
        """Upload a local directory to S3, skipping files that already exist with the same size.

        Args:
            local_dir:     Path to the local directory.
            remote_prefix: Target prefix in S3.
            bucket:        Bucket name; defaults to default_bucket.
            pattern:       Glob pattern for matching files; defaults to **/* (all subdirs).

        Returns:
            {"uploaded": N, "skipped": N, "failed": N, "files": {"uploaded": [...], "skipped": [...], "failed": [...]}}
        """
        from glob import glob

        bucket = bucket or self.default_bucket
        base_dir = Path(local_dir).resolve()
        uploaded, skipped, failed = [], [], []

        for local_file in glob(str(base_dir / pattern), recursive=True):
            if not os.path.isfile(local_file):
                continue
            rel_path = Path(local_file).resolve().relative_to(base_dir)
            remote_key = f"{remote_prefix}/{rel_path}" if remote_prefix else str(rel_path)
            remote_key = remote_key.replace("\\", "/")

            # Skip if file already exists in S3 with the same size
            if self.file_exists(remote_key, bucket):
                s3_info = self.get_file_info(remote_key, bucket)
                local_size = os.path.getsize(local_file)
                if s3_info["size"] == local_size:
                    skipped.append({"local": local_file, "key": remote_key, "reason": "size match"})
                    continue

            try:
                result = self.upload_file(local_file, remote_key, bucket)
                uploaded.append({"local": local_file, "key": remote_key})
            except Exception as e:
                failed.append({"local": local_file, "key": remote_key, "error": str(e)})

        return {
            "uploaded": len(uploaded),
            "skipped": len(skipped),
            "failed": len(failed),
            "files": {"uploaded": uploaded, "skipped": skipped, "failed": failed},
        }

"""
S3StorageClient - S3兼容存储客户端
支持 RustFS / MinIO / 阿里云 OSS / AWS S3 等
"""

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
    """
    S3兼容存储统一客户端

    使用示例:
        from s3_storage import S3StorageClient

        # 初始化（支持多节点）
        client = S3StorageClient(
            endpoint="http://localhost:9000",
            access_key="your_access_key",
            secret_key="your_secret_key",
            bucket="mybucket",
        )

        # 上传
        client.upload_file("/local/file.txt", "remote/file.txt")

        # 下载
        client.download_file("remote/file.txt", "/local/file.txt")

        # 列出文件
        files = client.list_files(prefix="folder/")
    """

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
        """
        初始化S3客户端

        Args:
            endpoint:   S3服务端点，如 http://localhost:9000
                       从环境变量 S3_ENDPOINT 读取
            access_key: AccessKey
                       从环境变量 S3_ACCESS_KEY 读取
            secret_key: SecretKey
                       从环境变量 S3_SECRET_KEY 读取
            region:     区域，默认 us-east-1
            bucket:     默认桶名
            bucket_prefix: 桶内路径前缀，如 "dev/"（自动添加到所有key前）
            timeout:       单次操作超时（秒）
            connect_timeout: 连接超时（秒）
        """
        self.endpoint = endpoint or os.getenv("S3_ENDPOINT")
        self.access_key = access_key or os.getenv("S3_ACCESS_KEY")
        self.secret_key = secret_key or os.getenv("S3_SECRET_KEY")
        self.region = region
        self.default_bucket = bucket or os.getenv("S3_BUCKET", "leapgo")
        self.bucket_prefix = bucket_prefix
        self.timeout = timeout
        self.connect_timeout = connect_timeout

        if not self.access_key or not self.secret_key:
            raise CredentialError(
                "缺少凭据：access_key 和 secret_key 不能为空，"
                "可传参数或设置环境变量 S3_ACCESS_KEY / S3_SECRET_KEY"
            )

        self._client = self._create_client()

    def _create_client(self):
        """创建boto3客户端"""
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
        """拼接bucket_prefix后的完整key"""
        return normalize_key(f"{self.bucket_prefix}/{key}").lstrip("/")

    # ── 桶操作 ────────────────────────────────────────────────

    def list_buckets(self) -> List[str]:
        """列出所有桶"""
        try:
            resp = self._client.list_buckets()
            return [b["Name"] for b in resp.get("Buckets", [])]
        except NoCredentialsError as e:
            raise CredentialError(f"认证失败: {e}") from e
        except ClientError as e:
            raise S3StorageError(f"列出桶失败: {e}") from e

    def bucket_exists(self, bucket: Optional[str] = None) -> bool:
        """检查桶是否存在"""
        bucket = bucket or self.default_bucket
        try:
            self._client.head_bucket(Bucket=bucket)
            return True
        except ClientError as e:
            return False

    # ── 文件操作 ────────────────────────────────────────────────

    def upload_file(
        self,
        local_path: str,
        remote_key: str,
        bucket: Optional[str] = None,
        content_type: Optional[str] = None,
        extra_args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        上传本地文件到S3

        Args:
            local_path:    本地文件路径
            remote_key:    存储到S3的key（不含bucket_prefix部分）
            bucket:        桶名，默认使用default_bucket
            content_type:  MIME类型，默认自动推断
            extra_args:    额外参数（如 Metadata, CacheControl 等）

        Returns:
            {"ETag": "...", "VersionId": "...", "key": "..."}
        """
        bucket = bucket or self.default_bucket
        key = self._full_key(remote_key)

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"本地文件不存在: {local_path}")

        content_type = content_type or guess_content_type(local_path)
        args = {"ContentType": content_type}
        if extra_args:
            args.update(extra_args)

        try:
            self._client.upload_file(local_path, bucket, key, ExtraArgs=args)
            file_size = os.path.getsize(local_path)
            # 计算MD5
            md5 = hashlib.md5(open(local_path, "rb").read()).hexdigest()
            return {
                "key": key,
                "bucket": bucket,
                "size": file_size,
                "md5": md5,
                "url": f"{self.endpoint}/{bucket}/{key}",
            }
        except ClientError as e:
            raise UploadError(f"上传失败 [{key}]: {e}") from e

    def upload_bytes(
        self,
        data: bytes,
        remote_key: str,
        bucket: Optional[str] = None,
        content_type: str = "application/octet-stream",
    ) -> Dict[str, Any]:
        """上传字节数据到S3"""
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
            raise UploadError(f"上传失败 [{key}]: {e}") from e

    def download_file(
        self,
        remote_key: str,
        local_path: str,
        bucket: Optional[str] = None,
    ) -> str:
        """
        从S3下载文件到本地

        Args:
            remote_key:  S3中的key
            local_path:  本地保存路径（包含文件名）
            bucket:      桶名

        Returns:
            本地文件路径
        """
        bucket = bucket or self.default_bucket
        key = self._full_key(remote_key)

        # 确保本地目录存在
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            self._client.download_file(bucket, key, local_path)
            return local_path
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey"):
                raise S3FileNotFoundError(f"S3文件不存在: {key}") from e
            raise DownloadError(f"下载失败 [{key}]: {e}") from e

    def delete_file(self, remote_key: str, bucket: Optional[str] = None) -> bool:
        """删除S3中的单个文件"""
        bucket = bucket or self.default_bucket
        key = self._full_key(remote_key)
        try:
            self._client.delete_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            raise S3StorageError(f"删除失败 [{key}]: {e}") from e

    def delete_files(self, remote_keys: List[str], bucket: Optional[str] = None) -> int:
        """批量删除文件，返回删除数量"""
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
            raise S3StorageError(f"批量删除失败: {e}") from e

    # ── 文件列表 ────────────────────────────────────────────────

    def list_files(
        self,
        prefix: str = "",
        bucket: Optional[str] = None,
        max_keys: int = 1000,
        include_size: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        列出桶内文件

        Args:
            prefix:     key前缀过滤
            bucket:     桶名
            max_keys:  最大返回数量
            include_size: 是否包含文件大小

        Returns:
            [{"key": "...", "size": 1234, "last_modified": "..."}, ...]
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
            raise S3StorageError(f"列出文件失败: {e}") from e

    def file_exists(self, remote_key: str, bucket: Optional[str] = None) -> bool:
        """检查文件是否存在"""
        bucket = bucket or self.default_bucket
        key = self._full_key(remote_key)
        try:
            self._client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    def get_file_info(self, remote_key: str, bucket: Optional[str] = None) -> Dict[str, Any]:
        """获取文件元信息（大小、最后修改时间、ETag等）"""
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
                raise S3FileNotFoundError(f"S3文件不存在: {key}") from e
            raise S3StorageError(f"获取文件信息失败 [{key}]: {e}") from e

    # ── 预签名链接 ──────────────────────────────────────────────

    def generate_presigned_url(
        self,
        remote_key: str,
        bucket: Optional[str] = None,
        expires_in: int = 604800,  # 7天
    ) -> str:
        """
        生成预签名访问URL（临时授权链接）

        Args:
            remote_key:  S3中的key
            bucket:      桶名
            expires_in:  有效期（秒），默认7天

        Returns:
            预签名URL
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
            raise S3StorageError(f"生成预签名URL失败 [{key}]: {e}") from e

    def generate_upload_presigned_url(
        self,
        remote_key: str,
        bucket: Optional[str] = None,
        expires_in: int = 3600,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        生成预签名上传URL（用于客户端直传S3）

        Args:
            remote_key:   S3中的key
            bucket:       桶名
            expires_in:  有效期（秒），默认1小时
            content_type: 上传文件的MIME类型

        Returns:
            预签名上传URL
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
            raise S3StorageError(f"生成上传URL失败 [{key}]: {e}") from e

    # ── 复制 / 移动 ─────────────────────────────────────────────

    def copy_file(
        self,
        src_key: str,
        dst_key: str,
        src_bucket: Optional[str] = None,
        dst_bucket: Optional[str] = None,
    ) -> Dict[str, Any]:
        """在S3内复制文件"""
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
            raise S3StorageError(f"复制失败 [{src_key}] -> [{dst_key}]: {e}") from e

    # ── 同步 ─────────────────────────────────────────────────

    def sync_upload(
        self,
        local_dir: str,
        remote_prefix: str = "",
        bucket: Optional[str] = None,
        pattern: str = "**/*",
    ) -> Dict[str, Any]:
        """
        同步本地目录到S3（只上传新文件/变更文件）

        Args:
            local_dir:     本地目录路径
            remote_prefix: S3中的目标前缀
            bucket:        桶名
            pattern:       文件匹配模式，默认 **/*（包含子目录）

        Returns:
            {"uploaded": N, "skipped": N, "failed": N, "files": [...]}
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

            # 检查S3中是否已存在且大小一致
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

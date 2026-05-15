"""自定义异常"""


class S3StorageError(Exception):
    """S3存储操作基异常"""
    pass


class CredentialError(S3StorageError):
    """凭据错误（AccessKey/SecretKey无效）"""
    pass


class BucketNotFoundError(S3StorageError):
    """桶不存在"""
    pass


class FileNotFoundError(S3StorageError):
    """文件不存在"""
    pass


class UploadError(S3StorageError):
    """上传失败"""
    pass


class DownloadError(S3StorageError):
    """下载失败"""
    pass

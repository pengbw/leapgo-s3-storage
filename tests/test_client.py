"""测试用例"""
import pytest
from s3_storage.exceptions import (
    S3StorageError,
    CredentialError,
    FileNotFoundError,
    UploadError,
    DownloadError,
)


class TestCredentialValidation:
    """凭据验证测试"""

    def test_missing_credential_raises_error(self):
        """缺少凭据时抛出 CredentialError"""
        with pytest.raises(CredentialError):
            from s3_storage import S3StorageClient
            S3StorageClient(endpoint="http://localhost:9000")

    def test_missing_secret_raises_error(self):
        """缺少 secret 时抛出 CredentialError"""
        with pytest.raises(CredentialError):
            from s3_storage import S3StorageClient
            S3StorageClient(endpoint="http://localhost:9000", access_key="xxx")


class TestUtils:
    """工具函数测试"""

    def test_normalize_key_strips_slashes(self):
        from s3_storage.utils import normalize_key
        assert normalize_key("a/b/c") == "a/b/c"
        assert normalize_key("/a/b/c/") == "a/b/c"
        assert normalize_key("a//b///c") == "a/b/c"

    def test_normalize_key_empty(self):
        from s3_storage.utils import normalize_key
        assert normalize_key("///") == ""

    def test_guess_content_type(self):
        from s3_storage.utils import guess_content_type
        assert guess_content_type("a.jpg") == "image/jpeg"
        assert guess_content_type("b.PDF") == "application/pdf"
        assert guess_content_type("c.unknown") == "application/octet-stream"

    def test_get_file_key(self):
        from s3_storage.utils import get_file_key
        key = get_file_key("/data/user/file.txt", "/data/user")
        assert key == "file.txt"

    def test_get_file_key_no_base(self):
        from s3_storage.utils import get_file_key
        key = get_file_key("/data/user/file.txt")
        assert key == "file.txt"


class TestExceptionsHierarchy:
    """异常体系测试"""

    def test_exception_hierarchy(self):
        assert issubclass(CredentialError, S3StorageError)
        assert issubclass(FileNotFoundError, S3StorageError)
        assert issubclass(UploadError, S3StorageError)
        assert issubclass(DownloadError, S3StorageError)

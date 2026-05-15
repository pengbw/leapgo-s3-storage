# Python 包结构

源码仓库：https://github.com/pengbw/leapgo-s3-storage

```
s3_storage/
├── __init__.py       # 导出 S3StorageClient, S3StorageError, CredentialError
├── client.py         # S3StorageClient 主体（约 300 行）
├── exceptions.py     # 自定义异常体系
└── utils.py          # normalize_key / get_file_key / guess_content_type
```

## S3StorageClient 主要方法

| 方法 | 说明 |
|------|------|
| `upload_file()` | 上传本地文件，含 MD5 校验 |
| `upload_bytes()` | 上传字节数据 |
| `download_file()` | 下载到本地路径 |
| `delete_file()` / `delete_files()` | 删除单个/批量删除 |
| `list_files()` | 列出桶内文件（支持 prefix 过滤） |
| `file_exists()` | 检查文件是否存在 |
| `get_file_info()` | 获取文件元信息（大小/MIME/ETag） |
| `generate_presigned_url()` | 生成访问链接（默认7天） |
| `generate_upload_presigned_url()` | 生成上传链接（默认1小时） |
| `copy_file()` | S3 内复制文件 |
| `sync_upload()` | 本地目录增量同步上传 |
| `list_buckets()` | 列出所有桶 |
| `bucket_exists()` | 检查桶是否存在 |

## 异常体系

```python
from s3_storage import S3StorageClient, S3StorageError, CredentialError

try:
    client = S3StorageClient(endpoint="http://localhost:9000", ...)
except CredentialError:
    # AccessKey/SecretKey 错误
except S3StorageError:
    # 其他 S3 操作错误
```

- `S3StorageError` — 基类
- `CredentialError` — 凭据错误
- `BucketNotFoundError` — 桶不存在
- `FileNotFoundError` — 文件不存在
- `UploadError` — 上传失败
- `DownloadError` — 下载失败

## 踩坑记录

1. **boto3 必须同时指定** `region_name='us-east-1'` + `Config(signature_version='s3v4')`，否则签名校验失败
2. **generate_presigned_url 的 Params**：`Bucket` 填桶名（如 `'leapgo'`），`Key` 填完整路径（如 `'开发/file.tar.gz'`），两者不能混淆
3. **key 规范**：自动 normalize（去除多余 `/`），但建议业务层保持统一格式
4. **bucket_prefix**：初始化时传入 `bucket_prefix='dev/'`，所有 key 自动加此前缀，适合多环境隔离

## 安装

```bash
pip install leapgo-s3-storage
```

或开发模式：
```bash
git clone https://github.com/pengbw/leapgo-s3-storage.git
cd leapgo-s3-storage
pip install -e .
```

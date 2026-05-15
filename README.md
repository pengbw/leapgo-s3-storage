# leapgo-s3-storage

S3 兼容对象存储 Python SDK，支持 RustFS / MinIO / 阿里云 OSS / AWS S3 等所有 S3 协议存储。

## 安装

```bash
pip install leapgo-s3-storage

# 或从源码安装
git clone https://github.com/pengbw/s3-storage.git
cd s3-storage
pip install -e .
```

## 快速开始

```python
from s3_storage import S3StorageClient

# 初始化
client = S3StorageClient(
    endpoint="http://localhost:9000",
    access_key="your_access_key",
    secret_key="your_secret_key",
    bucket="mybucket",
)

# 上传文件
client.upload_file("/local/file.txt", "remote/file.txt")

# 下载文件
client.download_file("remote/file.txt", "/local/save.txt")

# 列出文件
files = client.list_files(prefix="folder/")
for f in files:
    print(f"key={f['key']}, size={f['size']}")

# 生成分享链接（7天有效）
url = client.generate_presigned_url("remote/file.txt")

# 删除文件
client.delete_file("remote/file.txt")
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `S3_ENDPOINT` | 服务端点 | - |
| `S3_ACCESS_KEY` | AccessKey | - |
| `S3_SECRET_KEY` | SecretKey | - |
| `S3_BUCKET` | 默认桶名 | `leapgo` |

## 主要功能

- **文件上传/下载/删除**：支持本地文件、字节数据
- **批量操作**：批量删除、同步上传（只传变更文件）
- **预签名链接**：访问链接（默认7天）、上传链接（默认1小时）
- **文件管理**：列表、是否存在、元信息查询
- **S3 内复制**：同桶或跨桶复制
- **异常体系**：`CredentialError` / `FileNotFoundError` 等细分异常

## 踩坑记录

1. `boto3` 必须指定 `region_name='us-east-1'` + `Config(signature_version='s3v4')`，否则签名校验失败
2. `generate_presigned_url` 的 `Params`：`Bucket` 填桶名，`Key` 填完整路径，两者不能混淆
3. 建议业务层保持统一的 key 格式（无多余 `/`）

## License

MIT

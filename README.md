# leapgo-s3-storage

**它是做什么的：** 一个基于 `boto3` 的 S3 兼容对象存储 Python SDK，封装了上传、下载、删除、列表、预签名链接、增量同步等常用操作，开箱即用。

**支持哪些存储：** RustFS / MinIO / 阿里云 OSS / AWS S3 等所有兼容 S3 协议的对象存储服务。

## 安装

### 方式一：pip 安装（推荐）

```bash
pip install leapgo-s3-storage
```

### 方式二：从源码安装

```bash
# 克隆仓库
git clone https://github.com/pengbw/leapgo-s3-storage.git
cd leapgo-s3-storage

# 安装（开发模式，可编辑）
pip install -e .

# 或安装包含开发依赖
pip install -e ".[dev]"
```

### 方式三：直接引入（不安装）

如果不想安装，只需要在项目根目录执行：

```python
import sys
sys.path.insert(0, "/path/to/s3-storage/src")

from s3_storage import S3StorageClient
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

也可以不传参，从环境变量读取：

```python
import os
os.environ["S3_ENDPOINT"] = "http://localhost:9000"
os.environ["S3_ACCESS_KEY"] = "your_key"
os.environ["S3_SECRET_KEY"] = "your_secret"

client = S3StorageClient()  # 自动从环境变量读取
```

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

## Hermes Agent Skill 分发

本仓库同时包含 Hermes Agent Skill 文件，clone 后可给自己的 Hermes Agent 使用：

```bash
# 克隆仓库
git clone https://github.com/pengbw/leapgo-s3-storage.git

# 复制 skill 文件到 Hermes Agent 目录
cp -r skill/ ~/.hermes/skills/productivity/s3-storage/

# 重启 Hermes Agent 即可加载
```

Skill 包含：
- `SKILL.md` — 主入口，含配置说明和常用操作示例
- `references/python-package.md` — Python 包完整 API 文档
- `references/gh-push-workflow.md` — GitHub 推送工作流

## License

MIT

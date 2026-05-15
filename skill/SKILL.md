---
name: s3-storage
description: S3对象存储操作 - 连接、上传、下载、管理文件，支持RustFS/MinIO等S3兼容存储
category: productivity
---

# S3 Storage Skill

## 他人安装方式

从 GitHub 克隆后，把 `skill/` 目录下的文件复制到本地 Hermes Agent 对应目录即可使用：

```bash
# 克隆仓库
git clone https://github.com/pengbw/leapgo-s3-storage.git

# 复制 skill 文件到 Hermes Agent 目录
cp -r skill/ ~/.hermes/skills/productivity/s3-storage/

# 重启 Hermes Agent 即可加载
```

## Python 包（生产级）

源码已发布为 Python 包，地址：

**https://github.com/pengbw/leapgo-s3-storage**

```bash
pip install leapgo-s3-storage
```

完整 API 文档见 `references/python-package.md`。

---

## 配置

当前连接的 S3 服务：
- **Endpoint**: `http://localhost:9000`
- **Access Key**: `1Ub0U36ltFVTi4oQvoxl`
- **Secret Key**: `spY71j9B4Px3ELFVTEVd6rafLh5AmmdDB4Ng6KNc`
- **Region**: `us-east-1`
- **桶**: `leapgo`

## 环境准备

Python 虚拟环境已配置在 `~/.hermes/venv`

```python
import boto3
from botocore.config import Config

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='1Ub0U36ltFVTi4oQvoxl',
    aws_secret_access_key='spY71j9B4Px3ELFVTEVd6rafLh5AmmdDB4Ng6KNc',
    region_name='us-east-1',
    config=Config(signature_version='s3v4')
)
```

## 常用操作

### 1. 列出所有桶
```python
response = s3.list_buckets()
buckets = [b['Name'] for b in response['Buckets']]
```

### 2. 列出桶内文件
```python
objs = s3.list_objects_v2(Bucket='leapgo')
for obj in objs.get('Contents', []):
    print(f"{obj['Key']} - {obj['Size']} bytes")
```

### 3. 上传文件
```python
s3.upload_file('本地路径', 'leapgo', '存储的文件名')
# 或
with open('本地文件', 'rb') as f:
    s3.put_object(Bucket='leapgo', Key='文件名', Body=f)
```

### 4. 下载文件
```python
s3.download_file('leapgo', '文件名', '本地保存路径')
```

### 5. 删除文件
```python
s3.delete_object(Bucket='leapgo', Key='文件名')
```

### 6. 生成分享链接
```python
# 公开文件的临时访问链接（7天有效）
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'leapgo', 'Key': '文件名'},
    ExpiresIn=604800
)
```

## 完整使用示例

```python
#!/usr/bin/env python3
import boto3
from botocore.config import Config

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='1Ub0U36ltFVTi4oQvoxl',
    aws_secret_access_key='spY71j9B4Px3ELFVTEVd6rafLh5AmmdDB4Ng6KNc',
    region_name='us-east-1',
    config=Config(signature_version='s3v4')
)

BUCKET = 'leapgo'

# 上传文件
s3.upload_file('/path/to/local/file.txt', BUCKET, 'file.txt')

# 下载文件
s3.download_file(BUCKET, 'file.txt', '/path/to/save/file.txt')

# 列出所有文件
for obj in s3.list_objects_v2(Bucket=BUCKET).get('Contents', []):
    print(obj['Key'])
```

## 注意事项

1. RustFS 默认凭据在 `~/.hermes/venv` 环境下的 Python 脚本中使用
2. 桶 `leapgo` 是当前的默认存储桶
3. S3 路径风格使用 `path-style`（`/bucket/key`）而非 virtual-hosted-style
4. **踩坑记录**：`generate_presigned_url` 的 `Params` 中 `Bucket` 填存储桶名（如 `'leapgo'`），`Key` 填文件在桶内的完整路径（如 `'开发/file.tar.gz'`），两者不能混淆
5. **踩坑记录**：`boto3.client` 必须同时指定 `region_name='us-east-1'` 和 `config=Config(signature_version='s3v4')`，否则签名校验失败

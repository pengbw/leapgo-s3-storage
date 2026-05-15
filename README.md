# leapgo-s3-storage

**What it does:** A Python SDK for S3-compatible object storage, built on top of `boto3`. Provides ready-to-use wrappers for upload, download, delete, list, presigned URLs, and incremental sync.

**Supported storage backends:** RustFS / MinIO / Aliyun OSS / AWS S3 — any service that implements the S3 protocol.

## Install

### Option 1: pip (recommended)

```bash
pip install leapgo-s3-storage
```

### Option 2: from source

```bash
git clone https://github.com/pengbw/leapgo-s3-storage.git
cd leapgo-s3-storage
pip install -e .        # editable/dev mode
pip install -e ".[dev]" # with dev dependencies
```

### Option 3: import without installing

```python
import sys
sys.path.insert(0, "/path/to/s3-storage/src")

from s3_storage import S3StorageClient
```

## Quick Start

```python
from s3_storage import S3StorageClient

client = S3StorageClient(
    endpoint="http://localhost:9000",
    access_key="your_access_key",
    secret_key="your_secret_key",
    bucket="mybucket",
)

client.upload_file("/local/file.txt", "remote/file.txt")
client.download_file("remote/file.txt", "/local/save.txt")

files = client.list_files(prefix="folder/")
for f in files:
    print(f"key={f['key']}, size={f['size']}")

url = client.generate_presigned_url("remote/file.txt")  # valid 7 days
client.delete_file("remote/file.txt")
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `S3_ENDPOINT` | S3 endpoint URL | - |
| `S3_ACCESS_KEY` | Access key ID | - |
| `S3_SECRET_KEY` | Secret access key | - |
| `S3_REGION` | AWS region | `us-east-1` |
| `S3_BUCKET` | Default bucket name | `leapgo` |

```python
import os
os.environ["S3_ENDPOINT"] = "http://localhost:9000"
os.environ["S3_ACCESS_KEY"] = "your_key"
os.environ["S3_SECRET_KEY"] = "your_secret"

client = S3StorageClient()  # reads from env vars
```

## Key Features

- **Upload / Download / Delete**: local files, bytes, batch operations
- **Presigned URLs**: access URLs (default 7 days), upload URLs (default 1 hour)
- **File management**: list, exists check, metadata query
- **S3 copy**: same-bucket or cross-bucket copy
- **Incremental sync**: only uploads changed files (size check)
- **Exception hierarchy**: `CredentialError`, `FileNotFoundError`, `UploadError`, etc.

## Pitfalls

1. `boto3` requires both `region_name='us-east-1'` + `Config(signature_version='s3v4')` or signature verification fails
2. In `generate_presigned_url` `Params`: `Bucket` = bucket name (e.g. `'leapgo'`), `Key` = full path (e.g. `'folder/file.txt'`), don't mix them up
3. Keep key format consistent in your application — keys are normalized (redundant slashes removed) but not enforced

## Hermes Agent Skill Distribution

This repo also includes a Hermes Agent Skill. Clone and install it like this:

```bash
git clone https://github.com/pengbw/leapgo-s3-storage.git
cp -r skill/ ~/.hermes/skills/productivity/s3-storage/
# Restart Hermes Agent to load
```

Skill includes:
- `SKILL.md` — main entry with config and usage examples
- `references/python-package.md` — full Python SDK API reference
- `references/gh-push-workflow.md` — GitHub push workflow guide

## License

MIT

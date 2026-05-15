# Python Package Structure

Source repo: https://github.com/pengbw/leapgo-s3-storage

```
s3_storage/
├── __init__.py       # exports S3StorageClient, S3StorageError, CredentialError
├── client.py         # S3StorageClient main implementation (~300 lines)
├── exceptions.py     # exception hierarchy
└── utils.py          # normalize_key / get_file_key / guess_content_type
```

## S3StorageClient Main Methods

| Method | Description |
|--------|-------------|
| `upload_file()` | Upload a local file with MD5 checksum |
| `upload_bytes()` | Upload raw bytes |
| `download_file()` | Download to a local path |
| `delete_file()` / `delete_files()` | Delete single / batch delete |
| `list_files()` | List objects in bucket (prefix filter supported) |
| `file_exists()` | Check if a file exists |
| `get_file_info()` | Get file metadata (size / MIME / ETag) |
| `generate_presigned_url()` | Generate a temporary access URL (default 7 days) |
| `generate_upload_presigned_url()` | Generate an upload URL (default 1 hour) |
| `copy_file()` | Copy file within S3 |
| `sync_upload()` | Incrementally sync a local directory |
| `list_buckets()` | List all buckets |
| `bucket_exists()` | Check if a bucket exists |

## Exception Hierarchy

```python
from s3_storage import S3StorageClient, S3StorageError, CredentialError

try:
    client = S3StorageClient(endpoint="http://localhost:9000", ...)
except CredentialError:
    # access_key or secret_key is missing / invalid
except S3StorageError:
    # other S3 operation errors
```

- `S3StorageError` — base class
- `CredentialError` — credentials missing or invalid
- `BucketNotFoundError` — bucket does not exist
- `FileNotFoundError` — file/key does not exist in S3
- `UploadError` — upload operation failed
- `DownloadError` — download operation failed

## Pitfalls

1. **boto3 requires both** `region_name='us-east-1'` + `Config(signature_version='s3v4')`, otherwise signature verification fails
2. **generate_presigned_url Params**: `Bucket` = bucket name (e.g. `'leapgo'`), `Key` = full path (e.g. `'folder/file.tar.gz'`), don't mix them up
3. **Key format**: normalized automatically (redundant slashes stripped), but the application layer should keep a consistent format
4. **bucket_prefix**: pass `bucket_prefix='dev/'` at init — all keys will automatically be prefixed; useful for multi-environment isolation

## Install

```bash
pip install leapgo-s3-storage
```

Or dev mode:
```bash
git clone https://github.com/pengbw/leapgo-s3-storage.git
cd leapgo-s3-storage
pip install -e .
```

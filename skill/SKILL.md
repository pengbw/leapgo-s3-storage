---
name: s3-storage
description: S3 object storage operations — connect, upload, download, list, delete files; supports RustFS / MinIO / OSS / AWS S3 and any S3-compatible backend.
category: productivity
---

# S3 Storage Skill

## Installation for Other Users

Clone this repo and copy the `skill/` directory into your Hermes Agent skills folder:

```bash
git clone https://github.com/pengbw/leapgo-s3-storage.git
cp -r skill/ ~/.hermes/skills/productivity/s3-storage/

# Restart Hermes Agent to load
```

## Python Package (Production-Ready)

The source code is published as a pip package:

**https://github.com/pengbw/leapgo-s3-storage**

```bash
pip install leapgo-s3-storage
```

Full API reference: `references/python-package.md`.

---

## Configuration

Current S3 service in use:
- **Endpoint**: `http://localhost:9000`
- **Access Key**: `1Ub0U36ltFVTi4oQvoxl`
- **Secret Key**: `spY71j9B4Px3ELFVTEVd6rafLh5AmmdDB4Ng6KNc`
- **Region**: `us-east-1`
- **Bucket**: `leapgo`

## Environment Setup

Python virtual environment is at `~/.hermes/venv`.

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

## Common Operations

### 1. List all buckets
```python
response = s3.list_buckets()
buckets = [b['Name'] for b in response['Buckets']]
```

### 2. List objects in a bucket
```python
objs = s3.list_objects_v2(Bucket='leapgo')
for obj in objs.get('Contents', []):
    print(f"{obj['Key']} - {obj['Size']} bytes")
```

### 3. Upload a file
```python
s3.upload_file('local/path', 'leapgo', 'storage/key')
# or
with open('local/file', 'rb') as f:
    s3.put_object(Bucket='leapgo', Key='key', Body=f)
```

### 4. Download a file
```python
s3.download_file('leapgo', 'key', 'local/save/path')
```

### 5. Delete a file
```python
s3.delete_object(Bucket='leapgo', Key='key')
```

### 6. Generate a share link
```python
# Temporary access URL (valid 7 days)
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'leapgo', 'Key': 'key'},
    ExpiresIn=604800
)
```

## Full Example

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

s3.upload_file('/path/to/local/file.txt', BUCKET, 'file.txt')
s3.download_file(BUCKET, 'file.txt', '/path/to/save/file.txt')

for obj in s3.list_objects_v2(Bucket=BUCKET).get('Contents', []):
    print(obj['Key'])
```

## Notes

1. RustFS credentials are used in Python scripts running under `~/.hermes/venv`
2. Bucket `leapgo` is the current default storage bucket
3. S3 path-style is used (`/bucket/key`) rather than virtual-hosted-style
4. **Pitfall**: In `generate_presigned_url` `Params`, `Bucket` = bucket name (e.g. `'leapgo'`), `Key` = full path in bucket (e.g. `'folder/file.tar.gz'`), don't confuse the two
5. **Pitfall**: `boto3.client` requires both `region_name='us-east-1'` and `config=Config(signature_version='s3v4')`, otherwise signature verification fails

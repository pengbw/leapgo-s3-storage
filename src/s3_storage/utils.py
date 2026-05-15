"""Utility functions for S3 key normalization and content type detection."""

import re
from pathlib import Path
from typing import Optional


def normalize_key(key: str) -> str:
    """Normalize S3 key: strip leading/trailing slashes, collapse multiple slashes."""
    key = key.strip("/")
    key = re.sub(r"/+", "/", key)
    return key


def get_file_key(local_path: str, base_dir: Optional[str] = None) -> str:
    """Derive S3 key from a local file path.

    Args:
        local_path: e.g. /data/user/file.txt
        base_dir:   e.g. /data/user
        returns:    user/file.txt
    """
    path = Path(local_path).resolve()
    if base_dir:
        base = Path(base_dir).resolve()
        try:
            relative = path.relative_to(base)
            return str(relative).replace("\\", "/")
        except ValueError:
            return path.name
    return path.name


def guess_content_type(file_path: str) -> str:
    """Infer MIME type from file extension."""
    ext_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".pdf": "application/pdf",
        ".json": "application/json",
        ".html": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".txt": "text/plain",
        ".zip": "application/zip",
    }
    ext = Path(file_path).suffix.lower()
    return ext_map.get(ext, "application/octet-stream")

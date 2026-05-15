"""工具函数"""
import os
import re
from pathlib import Path
from typing import Optional


def normalize_key(key: str) -> str:
    """
    规范S3 key格式
    - 移除开头的 /
    - 移除多余的 /
    """
    key = key.strip("/")
    # 多个连续 / 合并为一个
    key = re.sub(r"/+", "/", key)
    return key


def get_file_key(local_path: str, base_dir: Optional[str] = None) -> str:
    """
    根据本地路径生成S3 key
    local_path: /data/user/file.txt
    base_dir:   /data/user
    return:     user/file.txt
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
    """根据文件扩展名猜测MIME类型"""
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

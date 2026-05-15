#!/usr/bin/env python3
"""
S3 操作演示脚本
用法: python scripts/demo.py

依赖: pip install leapgo-s3-storage
"""
import os
import sys

# 添加 src 目录到路径（开发时用）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from s3_storage import S3StorageClient

ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "1Ub0U36ltFVTi4oQvoxl")
SECRET_KEY = os.getenv("S3_SECRET_KEY", "spY71j9B4Px3ELFVTEVd6rafLh5AmmdDB4Ng6KNc")
BUCKET = os.getenv("S3_BUCKET", "leapgo")


def main():
    client = S3StorageClient(
        endpoint=ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        bucket=BUCKET,
    )
    print(f"✅ 连接成功: {ENDPOINT}")
    print(f"📦 桶: {BUCKET}")

    # 列出文件
    files = client.list_files(max_keys=5)
    print(f"\n📁 文件列表（前5个）:")
    for f in files:
        print(f"   {f['key']} ({f['size']} bytes)")
    if not files:
        print("   （空）")

    # 测试上传
    test_key = "test/demo.txt"
    test_content = b"Hello from leapgo-s3-storage!"
    result = client.upload_bytes(test_content, test_key)
    print(f"\n⬆️  上传成功: {result['key']}")

    # 生成链接
    url = client.generate_presigned_url(test_key)
    print(f"🔗 访问链接: {url[:80]}...")

    # 清理
    client.delete_file(test_key)
    print(f"\n🗑️  已删除: {test_key}")
    print("✅ 演示完成!")


if __name__ == "__main__":
    main()

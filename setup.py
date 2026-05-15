from setuptools import setup, find_packages

setup(
    name="leapgo-s3-storage",
    version="1.0.0",
    description="Python SDK for S3-compatible object storage (RustFS/MinIO/OSS/S3)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="LeapGo",
    author_email="leapgo@yeah.net",
    url="https://github.com/pengbw/leapgo-s3-storage",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=["boto3>=1.34.0", "botocore>=1.34.0"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

import os
import io
from abc import ABC, abstractmethod
from typing import BinaryIO, Union
from app.core.config import settings

class StorageService(ABC):
    @abstractmethod
    def save_file(self, file_content: bytes, destination_path: str) -> str:
        pass

    @abstractmethod
    def get_file(self, file_path: str) -> bytes:
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        pass

class LocalStorageService(StorageService):
    def __init__(self, base_dir: str = settings.STORAGE_LOCAL_DIR):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def save_file(self, file_content: bytes, destination_path: str) -> str:
        full_path = os.path.join(self.base_dir, destination_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(file_content)
        return destination_path

    def get_file(self, file_path: str) -> bytes:
        full_path = os.path.join(self.base_dir, file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(full_path, "rb") as f:
            return f.read()

    def file_exists(self, file_path: str) -> bool:
        full_path = os.path.join(self.base_dir, file_path)
        return os.path.exists(full_path)

class S3StorageService(StorageService):
    def __init__(self):
        import boto3
        from botocore.client import Config
        self.bucket_name = settings.S3_BUCKET_NAME
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1"
        )
        # Ensure bucket exists
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except Exception:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            except Exception:
                pass

    def save_file(self, file_content: bytes, destination_path: str) -> str:
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=destination_path,
            Body=file_content
        )
        return destination_path

    def get_file(self, file_path: str) -> bytes:
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_path)
        return response["Body"].read()

    def file_exists(self, file_path: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except Exception:
            return False

def get_storage_service() -> StorageService:
    if settings.STORAGE_TYPE == "s3" and settings.S3_ENDPOINT_URL:
        try:
            return S3StorageService()
        except Exception:
            return LocalStorageService()
    return LocalStorageService()

storage_service = get_storage_service()

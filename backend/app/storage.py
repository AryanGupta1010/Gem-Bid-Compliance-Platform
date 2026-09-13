import boto3
from botocore.exceptions import ClientError
from app.config import settings

class MinioClient:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=boto3.session.Config(signature_version='s3v4'),
        )
        self.doc_bucket = settings.MINIO_DOCUMENTS_BUCKET
        self.pages_bucket = settings.MINIO_PAGES_BUCKET
        self._ensure_bucket(self.doc_bucket)
        self._ensure_bucket(self.pages_bucket)

    def _ensure_bucket(self, bucket_name: str):
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except ClientError:
            self.s3_client.create_bucket(Bucket=bucket_name)

    def upload_file(self, file_path: str, object_name: str, bucket: str = None) -> str:
        b = bucket or self.doc_bucket
        self.s3_client.upload_file(file_path, b, object_name)
        return f"{b}/{object_name}"
        
    def upload_fileobj(self, file_obj, object_name: str, bucket: str = None) -> str:
        b = bucket or self.doc_bucket
        self.s3_client.upload_fileobj(file_obj, b, object_name)
        return f"{b}/{object_name}"
        
    def download_file_bytes(self, object_name: str, bucket: str = None) -> bytes:
        import io
        b = bucket or self.doc_bucket
        # MinIO paths stored in DB often include the bucket name as prefix if we used the upload return value.
        # e.g. "documents/bid_123/123_test.pdf"
        # We need to strip the bucket name if it's there.
        if object_name.startswith(f"{b}/"):
            object_name = object_name[len(b)+1:]
            
        file_obj = io.BytesIO()
        self.s3_client.download_fileobj(b, object_name, file_obj)
        return file_obj.getvalue()

minio_client = MinioClient()

from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://procureguard:password123@localhost:5432/procureguard_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: str = "password123"
    MINIO_SECURE: bool = False
    MINIO_DOCUMENTS_BUCKET: str = "documents"
    MINIO_PAGES_BUCKET: str = "rendered-pages"
    
    GST_API_URL: str = ""
    GST_API_KEY: str = ""
    
    AI_MODE: Literal['auto', 'real', 'demo'] = 'demo'
    MODEL_PROVIDER: str = "mock"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

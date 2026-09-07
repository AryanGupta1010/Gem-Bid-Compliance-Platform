import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "GeM AI Bid Compliance Platform"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "sih-2026-gem-compliance-super-secret-key-32charsmin!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Database: Default to sqlite if DATABASE_URL not set in env, fully compatible with postgresql:// in docker/prod
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./gem_compliance.db"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Storage / MinIO
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # 'local' or 's3'
    STORAGE_LOCAL_DIR: str = os.getenv("STORAGE_LOCAL_DIR", "./storage_data")
    S3_ENDPOINT_URL: Optional[str] = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    S3_ACCESS_KEY: Optional[str] = os.getenv("S3_ACCESS_KEY", "minioadmin")
    S3_SECRET_KEY: Optional[str] = os.getenv("S3_SECRET_KEY", "minioadmin")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "gem-bid-documents")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    DEMO_MODE: bool = True

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow"
    )

settings = Settings()

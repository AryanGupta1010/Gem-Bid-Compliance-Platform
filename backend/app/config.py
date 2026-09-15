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
    
    # AI Services Endpoints
    COLPALI_URL: str = "http://localhost:8002"
    SURYA_URL: str = "http://localhost:8003"
    SAUL_URL: str = "http://localhost:8004"
    NLI_URL: str = "http://localhost:8005"
    
    # AI Execution Mode ('live' requires running services; no silent mock fallback)
    AI_MODE: Literal['live', 'test', 'demo'] = 'live'
    MODEL_TIMEOUT: int = 60
    MODEL_MAX_RETRIES: int = 3
    
    # Government Verification Endpoints
    GST_API_URL: str = "http://localhost:8001/api/v1/gstin"
    GST_API_KEY: str = ""
    CPPP_API_URL: str = "http://localhost:8001/api/v1/cppp/status"
    UDYAM_API_URL: str = "http://localhost:8001/api/v1/udyam"
    
    # JWT Authentication
    JWT_SECRET: str = "procureguard-super-secret-jwt-key-2026-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()


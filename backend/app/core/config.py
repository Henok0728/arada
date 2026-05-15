"""
Central configuration — loaded once at startup.
All secrets come from environment variables, never from code.
"""
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lodge_link"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day for demo
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    API_KEY_HASH_ALGORITHM: str = "sha256"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://arada-rho.vercel.app",
        "https://arada.vercel.app",
        "https://arada-faqzwaex5-eyob2ones-projects.vercel.app",
    ]

    # SMS Gateway (AfricasTalking)
    AT_USERNAME: str = ""
    AT_API_KEY: str = ""
    AT_SENDER_ID: str = "LodgeLink"

    # Platform
    DEFAULT_COUNTRY: str = "ET"
    DEFAULT_CURRENCY: str = "ETB"
    REFERRAL_FANOUT_TIMEOUT_SECONDS: float = 3.0
    AVAILABILITY_CACHE_TTL_SECONDS: int = 90

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    def __init__(self, **values):
        super().__init__(**values)
        # Railway and other providers use postgres:// or postgresql://
        # but SQLAlchemy asyncpg needs postgresql+asyncpg://
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("postgres://"):
                self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
            elif self.DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in self.DATABASE_URL:
                self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Redis URL resolution for Railway/Production
        effective_redis = self.REDIS_URL or self.CELERY_BROKER_URL
        if not effective_redis or not any(effective_redis.startswith(s) for s in ["redis://", "rediss://", "unix://"]):
             # Final fallback to localhost only if absolutely no environment variable is found
             effective_redis = "redis://localhost:6379/0"
        
        self.REDIS_URL = effective_redis
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = effective_redis
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = effective_redis


settings = Settings()

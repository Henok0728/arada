"""
Central configuration — loaded once at startup.
All secrets come from environment variables, never from code.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lodge_link"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    API_KEY_HASH_ALGORITHM: str = "sha256"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

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

        # Redis URL safety check
        if not self.REDIS_URL or not any(self.REDIS_URL.startswith(s) for s in ["redis://", "rediss://", "unix://"]):
            # Fallback for demo if REDIS_URL is malformed or empty in Railway
            self.REDIS_URL = "redis://localhost:6379/0"


settings = Settings()

"""Application configuration, loaded from environment with sane local defaults."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "FSDIRAS"
    API_V1_PREFIX: str = "/api/v1"

    # Postgres in Docker; SQLite fallback so the suite runs before Docker is installed.
    DATABASE_URL: str = "sqlite:///./fsdiras.db"

    SECRET_KEY: str = "dev-only-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    ALGORITHM: str = "HS256"

    # REQ-3: configurable risk bands.
    RISK_MEDIUM_THRESHOLD: int = 40
    RISK_HIGH_THRESHOLD: int = 70

    ML_SERVICE_URL: str = "http://localhost:8001"

    # Local encrypted evidence store; swapped for S3 or equivalent on deploy.
    EVIDENCE_DIR: str = "./evidence_store"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

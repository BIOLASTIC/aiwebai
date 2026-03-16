import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "gemini_gateway.db"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="backend/.env", env_file_encoding="utf-8", extra="ignore")

    # ----- Network / Ports -----
    HOST: str = "0.0.0.0"
    API_PORT: int = 6400
    FRONTEND_PORT: int = 6401
    FLOWER_PORT: int = 6402
    MCP_PORT: int = 6403
    PROMETHEUS_PORT: int = 6404
    GRAFANA_PORT: int = 6405
    REDIS_PORT: int = 6406
    POSTGRES_PORT: int = 6407
    WEBSOCKET_PORT: int = 6408

    # ----- Application -----
    APP_NAME: str = "gemini-unified-gateway"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "change-me-to-a-64-char-random-string"
    MASTER_ENCRYPTION_KEY: str = "change-me-to-a-fernet-key"

    # ----- Database (SQLite) -----
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DB_PATH}"
    DATABASE_URL_SYNC: str = f"sqlite:///{DB_PATH}"

    # ----- Redis -----
    REDIS_HOST: str = "0.0.0.0"
    REDIS_PORT: int = 6406
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: str = "redis://0.0.0.0:6406/0"
    CELERY_BROKER_URL: str = "redis://0.0.0.0:6406/1"
    CELERY_RESULT_BACKEND: str = "redis://0.0.0.0:6406/2"

    # ----- JWT Auth -----
    JWT_SECRET: str = "change-me-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 1440
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # ----- Default Gemini Account (quick start) -----
    GEMINI_COOKIE_1PSID: Optional[str] = None
    GEMINI_COOKIE_1PSIDTS: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # ----- Rate Limiting -----
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_ACCOUNT_PER_MINUTE: int = 10
    RATE_LIMIT_STORAGE_URL: str = "redis://0.0.0.0:6406/3"

    # ----- CORS -----
    CORS_ORIGINS: List[str] = ["*"]

    # ----- Log Settings -----
    LOG_FILE: str = "logs/gateway.log"
    LOG_ROTATION: str = "50MB"
    LOG_RETENTION: int = 30
    LOG_FORMAT: str = "json"
    LOG_REDACT_PROMPTS: bool = True
    LOG_STORE_FULL_PAYLOADS: bool = False

settings = Settings()

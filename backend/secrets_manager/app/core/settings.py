"""
Settings module for FastAPI application.
Loads configuration from .env files using pydantic-settings.
"""

import os
from pathlib import Path
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.core.database import DatabaseSettings as DatabaseRuntime


# Determine the environment file path
# settings.py는 app/core/settings.py에 위치하므로
# ../../를 통해 secrets_manager 루트 디렉토리에 접근
SECRETS_MANAGER_ROOT = Path(__file__).resolve().parents[2]

# 환경 변수로 ENV 지정 (dev, staging, prod) - 기본값은 dev
ENV = os.getenv("ENV", "dev")
ENV_FILE = SECRETS_MANAGER_ROOT / f".env.{ENV}"

# 환경 파일이 없으면 .env.dev 사용
if not ENV_FILE.exists():
    ENV_FILE = SECRETS_MANAGER_ROOT / ".env.dev"


# ─────────────────────────────────────────────
#                 SETTINGS CLASSES
# ─────────────────────────────────────────────

class FastAPISettings(BaseSettings):
    NAME: str = Field(default="FastAPI Application")
    VERSION: str = Field(default="0.0.1")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="FASTAPI_",
        case_sensitive=True,
        extra="ignore",
    )


class CORSSettings(BaseSettings):
    ORIGINS: str = Field(default="")

    @property
    def origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ORIGINS.split(",")]
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="CORS_",
        case_sensitive=True,
        extra="ignore",
    )


class LoggingSettings(BaseSettings):
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE_PATH: str = Field(default="logs/app.log")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="LOG_",
        case_sensitive=True,
        extra="ignore",
    )


class DatabaseSettings(BaseSettings):
    USER: str = Field(default="postgres")
    PASSWORD: str = Field(default="postgres")
    NAME: str = Field(default="app_db")
    HOST: str = Field(default="localhost")
    PORT: int = Field(default=5432)

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"
    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="DB_",
        case_sensitive=True,
        extra="ignore",
    )


class SecuritySettings(BaseSettings):
    MASTER_KEY_PATH: str = Field(default="master.key")
    GRPC_TLS_ENABLED: bool = Field(default=False)  # 개발: False, 프로덕션: True
    GRPC_CA_CERT_PATH: str = Field(default="")
    GRPC_SERVER_CERT_PATH: str = Field(default="")
    GRPC_SERVER_KEY_PATH: str = Field(default="")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=True,
        extra="ignore",
    )

# ─────────────────────────────────────────────
#     LAZY-LOADED SETTINGS FACTORY FUNCTIONS
# ─────────────────────────────────────────────

@lru_cache
def get_fastapi_settings() -> FastAPISettings:
    return FastAPISettings()

@lru_cache
def get_cors_settings() -> CORSSettings:
    return CORSSettings()

@lru_cache
def get_logging_settings() -> LoggingSettings:
    return LoggingSettings()


@lru_cache
def get_database_settings() -> DatabaseRuntime:
    s = DatabaseSettings()
    return DatabaseRuntime(
        user=s.USER,
        password=s.PASSWORD,
        name=s.NAME,
        host=s.HOST,
        port=s.PORT,
    )

@lru_cache
def get_security_settings() -> SecuritySettings:
    return SecuritySettings()


__all__ = [
    "get_database_settings",
    "get_fastapi_settings",
    "get_cors_settings",
    "get_logging_settings",
]

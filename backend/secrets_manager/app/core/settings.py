"""
Settings module for FastAPI application.
Loads configuration from .env files using pydantic-settings.
"""

from pathlib import Path
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.core.database import DatabaseSettings as DatabaseRuntime


# Determine the environment file path
# SETTINGS_DIR = Path(__file__).resolve().parents[2] / "settings"
# ENV_FILE = SETTINGS_DIR / ".env"

ENV_FILE = "/workspaces/Highlighting/backend/secrets_manager/.env.dev"


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

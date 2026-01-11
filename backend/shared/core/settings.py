"""
Settings module for FastAPI application.
Loads configuration from .env files using pydantic-settings.
"""

from pathlib import Path
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..core.async_mail_client import AsyncEmailClient
from ..core.database import DatabaseSettings as DatabaseRuntime
from ..core.redis import RedisSettings as RedisRuntime


# Determine the environment file path
SETTINGS_DIR = Path(__file__).resolve().parents[2] / "settings"
ENV_FILE = SETTINGS_DIR / ".env.dev"


# ─────────────────────────────────────────────
#                 SETTINGS CLASSES
# ─────────────────────────────────────────────

class AppSettings(BaseSettings):
    NAME: str = Field(default="HiLi FastAPI MSA-Ready Boilerplate")
    VERSION: str = Field(default="0.0.1")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="APP_",
        case_sensitive=True,
        extra="ignore",
    )


class CORSSettings(BaseSettings):
    ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
    )
    ALLOW_CREDENTIALS: bool = Field(default=True)

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


class AuthSettings(BaseSettings):
    BCRYPT_ROUNDS: int = Field(default=12)
    # SECRET_KEY_PATH: str = Field(default="./app/api/v1/auth/tools/jwt_secret.key")
    RSA_PRIVATE_KEY_PATH: str = Field(default="./")  # BasePath 만 작성 (파일 명 자동 생성)
    RSA_PUBLIC_KEY_PATH: str = Field(default="./")  # BasePath 만 작성 (파일 명 자동 생성)
    SECRET_KEY_ROTATION_DAYS: int = Field(default=30)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)

    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    REFRESH_TOKEN_STORE_HASHED: bool = Field(default=False)
    REFRESH_TOKEN_BYTE_LENGTH: int = Field(default=32)

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="AUTH_",
        case_sensitive=True,
        extra="ignore",
        populate_by_name=True,
    )


class CookieSettings(BaseSettings):
    SECURE: bool = Field(default=True)
    SAMESITE: str = Field(default="none")
    PATH: str = Field(default="/")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="COOKIE_",
        case_sensitive=True,
        extra="ignore",
    )


class EmailVerifySettings(BaseSettings):
    VERIFY_TOKEN_EXPIRE_MINUTES: int = Field(default=10)
    VERIFY_CODE_LENGTH: int = Field(default=16)

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="EMAIL_",
        case_sensitive=True,
        extra="ignore",
    )


class GoogleOAuthSettings(BaseSettings):
    OAUTH_CLIENT_ID: str = Field(...)
    OAUTH_CLIENT_SECRET: str = Field(...)
    OAUTH_REDIRECT_URI: str = Field(default="postmessage")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="GOOGLE_",
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


class RedisSettings(BaseSettings):
    HOST: str = Field(...)
    PORT: int = Field(default=6379)
    DB: int = Field(default=0)
    USER: str = Field(default="default")
    PASSWORD: Optional[str] = Field(None)
    @property
    def redis_url(self) -> str:
        if self.PASSWORD:
            if self.USER and self.USER != "default":
                return f"redis://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"
            return f"redis://:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"
        return f"redis://{self.HOST}:{self.PORT}/{self.DB}"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="REDIS_",
        case_sensitive=True,
        extra="ignore",
    )


class SMTPSettings(BaseSettings):
    HOST: str = Field(default="smtp.gmail.com")
    PORT: int = Field(default=587)
    USER: str = Field(...)
    PASSWORD: str = Field(...)

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="SMTP_",
        case_sensitive=True,
        extra="ignore",
    )


# ─────────────────────────────────────────────
#     LAZY-LOADED SETTINGS FACTORY FUNCTIONS
# ─────────────────────────────────────────────

@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()

@lru_cache
def get_cors_settings() -> CORSSettings:
    return CORSSettings()

@lru_cache
def get_logging_settings() -> LoggingSettings:
    return LoggingSettings()

@lru_cache
def get_auth_settings() -> AuthSettings:
    return AuthSettings()

@lru_cache
def get_cookie_settings() -> CookieSettings:
    return CookieSettings()

@lru_cache
def get_email_verify_settings() -> EmailVerifySettings:
    return EmailVerifySettings()

@lru_cache
def get_google_oauth_settings() -> GoogleOAuthSettings:
    return GoogleOAuthSettings()

@lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()

@lru_cache
def get_redis_settings() -> RedisSettings:
    return RedisSettings()

@lru_cache
def get_smtp_settings() -> SMTPSettings:
    return SMTPSettings()


# ─────────────────────────────────────────────
#       RUNTIME CONFIG (DEPENDENT SETTINGS)
# ─────────────────────────────────────────────

@lru_cache
def get_database_runtime() -> DatabaseRuntime:
    s = get_database_settings()
    return DatabaseRuntime(
        user=s.USER,
        password=s.PASSWORD,
        name=s.NAME,
        host=s.HOST,
        port=s.PORT,
    )


@lru_cache
def get_smtp_runtime() -> AsyncEmailClient.EmailClientConfig:
    s = get_smtp_settings()
    return AsyncEmailClient.EmailClientConfig(
        smtp_host=s.HOST,
        smtp_port=s.PORT,
        username=s.USER,
        password=s.PASSWORD,
        from_email=s.USER,
        use_tls=True,
    )


@lru_cache
def get_redis_runtime() -> RedisRuntime:
    s = get_redis_settings()
    return RedisRuntime(
        host=s.HOST,
        port=s.PORT,
        db=s.DB,
        user=s.USER,
        password=s.PASSWORD,
    )


__all__ = [
    "get_app_settings",
    "get_cors_settings",
    "get_logging_settings",
    "get_auth_settings",
    "get_cookie_settings",
    "get_email_verify_settings",
    "get_google_oauth_settings",
    "get_database_settings",
    "get_redis_settings",
    "get_smtp_settings",
    "get_database_runtime",
    "get_redis_runtime",
    "get_smtp_runtime",
]

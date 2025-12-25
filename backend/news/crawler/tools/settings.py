from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    naver_client_id: str = Field(..., description="Naver API Client ID")
    naver_client_secret: str = Field(..., description="Naver API Client Secret")

    # overload env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
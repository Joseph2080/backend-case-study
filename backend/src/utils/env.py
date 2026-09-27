from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: Literal["development", "production"] = "development"

    DB_URL: str = "postgresql+asyncpg://case_study:case_study@127.0.0.1:55432/case_study"

    OPENAI_API_KEY: SecretStr = Field(default=..., min_length=1)


env = Settings()

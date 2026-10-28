from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    test_database_url: str | None = None
    cors_origins: list[str] = ["http://localhost:3001"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

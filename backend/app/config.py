from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    tavily_api_key: str = ""
    aviationstack_api_key: str = ""

    default_origin_city: str = "Dhaka"

    database_url: str = ""
    """Optional. When unset, trip threads are checkpointed in memory only."""

    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

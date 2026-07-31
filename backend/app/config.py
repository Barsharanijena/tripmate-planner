from functools import lru_cache

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# pydantic-settings below only reads .env into this module's own Settings
# fields — it does not export values to the real process environment. Several
# SDKs used by this app (LangSmith tracing, Tavily's client) read their config
# directly from os.environ instead of accepting it as a constructor kwarg, so
# .env has to be loaded into the process environment too, not just parsed
# into our own model.
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    tavily_api_key: str = ""
    aviationstack_api_key: str = ""

    amadeus_api_key: str = ""
    amadeus_api_secret: str = ""
    """Optional. When both are set, real bookable flight fares (Amadeus) are used instead of
    AviationStack's live-status-only data."""

    langsmith_api_key: str = ""
    langsmith_project: str = "tripmate-planner"
    """Optional. When set, every graph run (and the LLM calls inside it) is traced to LangSmith."""

    default_origin_city: str = "Pune"

    database_url: str = ""
    """Optional. When unset, trip threads are checkpointed in memory only."""

    cors_origins: list[str] = ["http://localhost:5173"]
    """Comma-separated in env, e.g. CORS_ORIGINS=https://myapp.vercel.app,http://localhost:5173"""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

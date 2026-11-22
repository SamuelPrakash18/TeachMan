from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://teachman:teachman@localhost:5432/teachman"
    jwt_secret: str = "dev-only-change-me"
    jwt_expire_minutes: int = 60 * 12
    cors_origins: str = "http://localhost:5173"
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    nvidia_timeout_seconds: int = 180
    nvidia_max_tokens: int = 2048
    nvidia_reasoning_budget: int = 2048
    nvidia_enable_thinking: bool = False

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        if isinstance(value, str):
            if value.startswith("postgresql://"):
                return "postgresql+psycopg://" + value[len("postgresql://"):]
            if value.startswith("postgres://"):
                return "postgresql+psycopg://" + value[len("postgres://"):]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

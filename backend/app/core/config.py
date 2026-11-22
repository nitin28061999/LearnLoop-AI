from functools import lru_cache
from typing import Any, Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict  # pyright: ignore[reportMissingImports]


class Settings(BaseSettings):
    app_name: str = "LearnLoop AI"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    environment: Literal["development", "production", "testing"] = "development"
    debug: bool = True

    supabase_url: str | None = None
    supabase_publishable_key: SecretStr | None = None
    supabase_secret_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(
        self,
        _env_file: str | None = None,
        **values: Any,
    ) -> None:
        super().__init__(_env_file=_env_file, **values)


@lru_cache
def get_settings() -> Settings:
    return Settings()

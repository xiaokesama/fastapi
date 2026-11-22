from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    app_name: str = "StudyTrack 学习打卡"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    secret_key: str = "dev-only-change-this-secret-key-before-production-2026"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    database_url: str = "sqlite+aiosqlite:///./study_tracker.db"
    auto_create_tables: bool = True
    sql_echo: bool = False

    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
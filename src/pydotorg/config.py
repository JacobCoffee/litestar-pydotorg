"""Application configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    debug: bool = False
    secret_key: str = "change-me-in-production"  # noqa: S105
    site_name: str = "Python.org"
    site_description: str = "The official home of the Python Programming Language"
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "python.org", "*.python.org"]

    database_url: PostgresDsn = "postgresql+asyncpg://postgres:postgres@localhost:5432/pydotorg"  # type: ignore[assignment]
    database_pool_size: int = 20
    database_max_overflow: int = 10

    redis_url: str = "redis://localhost:6379/0"

    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24 * 7

    static_url: str = "/static"
    media_url: str = "/media"
    static_dir: Path = BASE_DIR / "static"
    media_dir: Path = BASE_DIR / "media"
    templates_dir: Path = BASE_DIR / "src" / "pydotorg" / "templates"

    python_blog_feed_url: str = "https://blog.python.org/feeds/posts/default?alt=rss"
    python_blog_url: str = "https://blog.python.org"

    fastly_api_key: str | None = None

    @computed_field
    @property
    def database_url_sync(self) -> str:
        return str(self.database_url).replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

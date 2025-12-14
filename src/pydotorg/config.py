"""Application configuration."""

from __future__ import annotations

import logging
from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic import (
    BaseModel,
    Field,
    PostgresDsn,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
logger = logging.getLogger(__name__)

UNSAFE_DEFAULT_SECRETS = {
    "change-me-in-production",
    "change-me-in-production-session",
    "change-me-csrf-secret",
    "insecure-secret-key",
    "dev-secret",
    "secret",
}
MIN_SECRET_KEY_LENGTH = 32


class Environment(str, Enum):
    """Application environment."""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class FeatureFlagsConfig(BaseModel):
    """Feature flags configuration for conditional functionality."""

    enable_oauth: bool = True
    enable_jobs: bool = True
    enable_sponsors: bool = True
    enable_search: bool = True
    maintenance_mode: bool = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Environment = Field(
        default=Environment.DEV,
        validation_alias="APP_ENV",
        description="Application environment (dev/staging/prod)",
    )

    debug: bool | None = Field(
        default=None,
        description="Enable debug mode (auto-set based on environment if not specified)",
    )
    secret_key: str = "change-me-in-production"  # noqa: S105
    site_name: str = "Python.org"
    site_description: str = "The official home of the Python Programming Language"
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "python.org", "*.python.org"]

    database_url: PostgresDsn = "postgresql+asyncpg://postgres:postgres@localhost:5432/pydotorg"  # type: ignore[assignment]
    database_pool_size: int = 20
    database_max_overflow: int = 10

    redis_url: str = "redis://localhost:6379/0"
    worker_concurrency: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of concurrent SAQ workers",
    )
    saq_worker_concurrency: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of concurrent SAQ workers for litestar-saq plugin",
    )
    saq_web_enabled: bool = Field(
        default=False,
        description="Enable SAQ built-in web UI (disabled - using custom admin UI)",
    )

    log_format: str = Field(
        default="console",
        description="Logging format: 'console' for development, 'json' for production",
    )
    log_file: Path | None = Field(
        default=None,
        description="Optional log file path for file-based logging",
    )

    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24 * 7

    github_client_id: str | None = None
    github_client_secret: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    oauth_redirect_base_url: str = "http://localhost:8000"

    session_secret_key: str = "change-me-in-production-session"  # noqa: S105
    session_expire_minutes: int = 60 * 24 * 7
    session_cookie_name: str = "session_id"

    csrf_secret: str = "change-me-csrf-secret"  # noqa: S105
    csrf_cookie_name: str = "csrftoken"
    csrf_header_name: str = "x-csrftoken"

    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@python.org"
    smtp_from_name: str = "Python.org"
    smtp_use_tls: bool = True
    email_verification_expire_hours: int = 24
    jobs_admin_email: str = "jobs@python.org"
    events_admin_email: str = "events@python.org"

    static_url: str = "/static"
    media_url: str = "/media"
    static_dir: Path = BASE_DIR / "static"
    media_dir: Path = BASE_DIR / "media"
    templates_dir: Path = BASE_DIR / "src" / "pydotorg" / "templates"

    python_blog_feed_url: str = "https://blog.python.org/feeds/posts/default?alt=rss"
    python_blog_url: str = "https://blog.python.org"

    fastly_api_key: str | None = None

    meilisearch_url: str = "http://127.0.0.1:7700"
    meilisearch_api_key: str | None = None
    meilisearch_index_prefix: str = "pydotorg_"

    features: FeatureFlagsConfig = FeatureFlagsConfig()

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Ensure secret key is secure in production."""
        environment = info.data.get("environment", Environment.DEV)

        if environment in (Environment.PROD, Environment.STAGING):
            if v in UNSAFE_DEFAULT_SECRETS:
                msg = f"SECRET_KEY must be changed in {environment.value} environment"
                raise ValueError(msg)
            if len(v) < MIN_SECRET_KEY_LENGTH:
                msg = (
                    f"SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters in {environment.value} environment"
                )
                raise ValueError(msg)

        return v

    @field_validator("session_secret_key")
    @classmethod
    def validate_session_secret_key(cls, v: str, info) -> str:
        """Ensure session secret key is secure in production."""
        environment = info.data.get("environment", Environment.DEV)

        if environment in (Environment.PROD, Environment.STAGING):
            if v in UNSAFE_DEFAULT_SECRETS:
                msg = f"SESSION_SECRET_KEY must be changed in {environment.value} environment"
                raise ValueError(msg)
            if len(v) < MIN_SECRET_KEY_LENGTH:
                msg = f"SESSION_SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters in {environment.value} environment"
                raise ValueError(msg)

        return v

    @field_validator("csrf_secret")
    @classmethod
    def validate_csrf_secret(cls, v: str, info) -> str:
        """Ensure CSRF secret is secure in production."""
        environment = info.data.get("environment", Environment.DEV)

        if environment in (Environment.PROD, Environment.STAGING):
            if v in UNSAFE_DEFAULT_SECRETS:
                msg = f"CSRF_SECRET must be changed in {environment.value} environment"
                raise ValueError(msg)
            if len(v) < MIN_SECRET_KEY_LENGTH:
                msg = f"CSRF_SECRET must be at least {MIN_SECRET_KEY_LENGTH} characters in {environment.value} environment"
                raise ValueError(msg)

        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: PostgresDsn) -> PostgresDsn:
        """Ensure database URL is valid PostgreSQL."""
        url_str = str(v)
        if not url_str.startswith(("postgresql://", "postgresql+asyncpg://")):
            msg = "DATABASE_URL must be a valid PostgreSQL URL"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_production_config(self) -> Settings:
        """Cross-field validation for production safety."""
        if self.environment in (Environment.PROD, Environment.STAGING):
            if self.debug:
                msg = f"DEBUG mode must be disabled in {self.environment.value} environment"
                raise ValueError(msg)

            db_url = str(self.database_url)
            if "postgres:postgres@" in db_url or ("localhost" in db_url and self.environment == Environment.PROD):
                msg = f"Default database credentials or localhost detected in {self.environment.value} environment"
                raise ValueError(msg)

        return self

    @computed_field
    @property
    def is_debug(self) -> bool:
        """Determine debug status based on environment if not explicitly set."""
        if self.debug is not None:
            return self.debug
        return self.environment == Environment.DEV

    @computed_field
    @property
    def create_all(self) -> bool:
        """Auto-create database tables on startup (dev only)."""
        return self.environment == Environment.DEV

    @computed_field
    @property
    def log_level(self) -> str:
        """Log level based on environment."""
        if self.environment == Environment.DEV:
            return "DEBUG"
        if self.environment == Environment.STAGING:
            return "INFO"
        return "WARNING"

    @computed_field
    @property
    def use_json_logging(self) -> bool:
        """Use JSON logging format in production, console in development."""
        if self.log_format == "json":
            return True
        if self.log_format == "console":
            return False
        return self.environment == Environment.PROD

    @computed_field
    @property
    def show_error_details(self) -> bool:
        """Show detailed error messages (dev/staging only)."""
        return self.environment in {Environment.DEV, Environment.STAGING}

    @computed_field
    @property
    def cors_allow_all(self) -> bool:
        """Allow all CORS origins (dev only)."""
        return self.environment == Environment.DEV

    @computed_field
    @property
    def database_url_sync(self) -> str:
        return str(self.database_url).replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def get_config_warnings() -> list[str]:
    """Get list of configuration warnings."""
    cfg = get_settings()
    warnings: list[str] = []

    if not cfg.fastly_api_key:
        warnings.append("CDN disabled (no FASTLY_API_KEY)")

    if not cfg.smtp_host:
        warnings.append("Email disabled (no SMTP_HOST configured)")

    if cfg.redis_url == "redis://localhost:6379/0" and cfg.environment == Environment.PROD:
        warnings.append("Default Redis URL in production")

    if not cfg.github_client_id or not cfg.github_client_secret:
        warnings.append("GitHub OAuth disabled")

    if not cfg.google_client_id or not cfg.google_client_secret:
        warnings.append("Google OAuth disabled")

    return warnings


def validate_production_settings() -> None:
    """Validate production settings (raises in prod if critical settings missing)."""
    cfg = get_settings()

    if cfg.environment == Environment.PROD:
        if cfg.secret_key in UNSAFE_DEFAULT_SECRETS:
            msg = "Production deployment with unsafe default SECRET_KEY"
            raise ValueError(msg)
        if cfg.session_secret_key in UNSAFE_DEFAULT_SECRETS:
            msg = "Production deployment with unsafe default SESSION_SECRET_KEY"
            raise ValueError(msg)


def log_startup_banner() -> None:
    """Print application startup information directly to stdout."""
    import os  # noqa: PLC0415
    import sys  # noqa: PLC0415

    cfg = get_settings()
    warnings = get_config_warnings()

    db_hosts = cfg.database_url.hosts()
    db_info = db_hosts[0] if db_hosts else {}
    db_host = db_info.get("host", "unknown")
    db_port = db_info.get("port", 5432)
    db_name = cfg.database_url.path.lstrip("/") if cfg.database_url.path else "unknown"
    redis_display = cfg.redis_url.split("@")[-1] if "@" in cfg.redis_url else cfg.redis_url

    # Show MailDev UI URL in dev mode when using local SMTP on port 1025
    if cfg.environment == Environment.DEV and cfg.smtp_port == 1025:
        email_display = "http://localhost:1080 (MailDev)"
    else:
        email_display = f"{cfg.smtp_host}:{cfg.smtp_port}"

    def _bool_icon(*, val: bool) -> str:
        return "\033[92m✓\033[0m" if val else "\033[91m✗\033[0m"

    warnings_section = ""
    if warnings:
        warnings_list = "\n".join(f"  \033[93m⚠\033[0m {w}" for w in warnings)
        warnings_section = f"\n\033[1mWarnings:\033[0m\n{warnings_list}\n"

    banner = f"""
\033[94m╔══════════════════════════════════════════════════════════════╗
║                 \033[93m🐍  {cfg.site_name:^20}  🐍\033[94m                 ║
╚══════════════════════════════════════════════════════════════╝\033[0m

\033[1mServer:\033[0m
  URL:              http://localhost:8000
  API Docs:         http://localhost:8000/api/docs
  Admin:            http://localhost:8000/admin
  PID:              {os.getpid()}
  Environment:      {cfg.environment.value.upper()}
  Debug Mode:       {_bool_icon(val=cfg.is_debug)} {cfg.is_debug}
  Log Level:        {cfg.log_level}

\033[1mConnections:\033[0m
  Database:         postgresql://{db_host}:{db_port}/{db_name}
  Redis:            {redis_display}

\033[1mSecurity:\033[0m
  Create Tables:    {_bool_icon(val=cfg.create_all)} {cfg.create_all}
  CORS Allow All:   {_bool_icon(val=cfg.cors_allow_all)} {cfg.cors_allow_all}
  Error Details:    {_bool_icon(val=cfg.show_error_details)} {cfg.show_error_details}

\033[1mFeatures:\033[0m
  CDN:              {_bool_icon(val=bool(cfg.fastly_api_key))}
  Email:            {_bool_icon(val=bool(cfg.smtp_host))} {email_display}
  GitHub OAuth:     {_bool_icon(val=bool(cfg.github_client_id))}
  Google OAuth:     {_bool_icon(val=bool(cfg.google_client_id))}
  Meilisearch:      {_bool_icon(val=bool(cfg.meilisearch_url))} {cfg.meilisearch_url}
  Jobs:             {_bool_icon(val=cfg.features.enable_jobs)}
  Sponsors:         {_bool_icon(val=cfg.features.enable_sponsors)}
  Search:           {_bool_icon(val=cfg.features.enable_search)}
  Maintenance:      {_bool_icon(val=cfg.features.maintenance_mode)}
{warnings_section}
\033[92m✓ Application ready\033[0m
"""
    sys.stdout.write(banner)
    sys.stdout.flush()


def get_config_summary() -> dict[str, str | bool | int]:
    """Get non-sensitive configuration summary for admin endpoint."""
    cfg = get_settings()

    db_hosts = cfg.database_url.hosts()
    db_info = db_hosts[0] if db_hosts else {}

    return {
        "environment": cfg.environment.value,
        "debug": cfg.is_debug,
        "log_level": cfg.log_level,
        "database_host": db_info.get("host", "unknown"),
        "database_port": db_info.get("port", 5432),
        "database_name": cfg.database_url.path.lstrip("/") if cfg.database_url.path else "unknown",
        "redis_configured": bool(cfg.redis_url and cfg.redis_url != "redis://localhost:6379/0"),
        "cdn_enabled": bool(cfg.fastly_api_key),
        "email_enabled": bool(cfg.smtp_host),
        "github_oauth_enabled": bool(cfg.github_client_id),
        "google_oauth_enabled": bool(cfg.google_client_id),
        "create_tables_on_startup": cfg.create_all,
        "cors_allow_all": cfg.cors_allow_all,
        "show_error_details": cfg.show_error_details,
        "jwt_algorithm": cfg.jwt_algorithm,
        "session_expire_minutes": cfg.session_expire_minutes,
        "features": {
            "enable_oauth": cfg.features.enable_oauth,
            "enable_jobs": cfg.features.enable_jobs,
            "enable_sponsors": cfg.features.enable_sponsors,
            "enable_search": cfg.features.enable_search,
            "maintenance_mode": cfg.features.maintenance_mode,
        },
    }

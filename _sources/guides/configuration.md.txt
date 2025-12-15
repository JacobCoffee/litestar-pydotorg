# Configuration Guide

This guide covers environment configuration and settings for litestar-pydotorg.

## Environment Variables

Configuration is managed through environment variables, typically defined in a `.env` file for local development.

### Core Settings

```bash
# Application mode
DEBUG=true                    # Enable debug mode
ENVIRONMENT=development       # Environment name (development, staging, production)

# Secret key for security (JWT, session signing)
SECRET_KEY=your-secure-secret-key-here
```

### Database Configuration

```bash
# PostgreSQL connection
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pydotorg

# Connection pool settings
DATABASE_POOL_SIZE=5          # Minimum pool size
DATABASE_MAX_OVERFLOW=10      # Maximum overflow connections

# Query logging
DATABASE_ECHO=false           # Log all SQL queries
```

### Redis Configuration

```bash
# Redis connection
REDIS_URL=redis://localhost:6379/0

# Cache settings
CACHE_TTL=3600                # Default cache TTL in seconds
```

### Server Settings

```bash
# Host and port
HOST=0.0.0.0
PORT=8000

# Workers (for production)
WORKERS=4                     # Number of worker processes
```

### Logging

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log format (json, text)
LOG_FORMAT=json
```

### Feature Flags

```bash
# Feature toggles (see Feature Flags guide)
FEATURES__ENABLE_OAUTH=true
FEATURES__ENABLE_JOBS=true
FEATURES__ENABLE_SPONSORS=true
FEATURES__ENABLE_SEARCH=true
FEATURES__MAINTENANCE_MODE=false
```

### OAuth Providers

```bash
# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Email Configuration

```bash
# SMTP settings
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=noreply@python.org
SMTP_TLS=true
```

### External Services

```bash
# Meilisearch (search)
MEILISEARCH_URL=http://localhost:7700
MEILISEARCH_API_KEY=your-api-key

# Sentry (error tracking)
SENTRY_DSN=https://your-sentry-dsn

# CDN
CDN_URL=https://cdn.python.org
```

## Configuration Class

Settings are managed using Pydantic Settings:

```python
# src/pydotorg/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    # Core
    debug: bool = False
    environment: str = "development"
    secret_key: str

    # Database
    database_url: str
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Feature flags
    features: FeatureFlagsConfig = FeatureFlagsConfig()


# Singleton instance
settings = Settings()
```

## Accessing Settings

### In Application Code

```python
from pydotorg.config import settings

if settings.debug:
    logger.debug("Debug mode enabled")

database_url = settings.database_url
```

### In Templates

Settings can be exposed to templates via context processors:

```python
# Template context processor
def settings_context(request: Request) -> dict:
    return {
        "debug": settings.debug,
        "environment": settings.environment,
    }
```

```jinja
{% if debug %}
<div class="debug-banner">Debug Mode</div>
{% endif %}
```

## Environment-Specific Configuration

### Development

```bash
# .env.development
DEBUG=true
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pydotorg_dev
DATABASE_ECHO=true
LOG_LEVEL=DEBUG
```

### Testing

```bash
# .env.test
DEBUG=true
ENVIRONMENT=test
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pydotorg_test
LOG_LEVEL=WARNING
```

### Staging

```bash
# .env.staging
DEBUG=false
ENVIRONMENT=staging
DATABASE_URL=postgresql+asyncpg://user:pass@staging-db:5432/pydotorg
LOG_LEVEL=INFO
SENTRY_DSN=https://staging-sentry-dsn
```

### Production

```bash
# .env.production
DEBUG=false
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://user:pass@production-db:5432/pydotorg
LOG_LEVEL=WARNING
WORKERS=8
SENTRY_DSN=https://production-sentry-dsn
```

## Secrets Management

### Local Development

Store secrets in `.env` file (never commit to git):

```bash
# .env (gitignored)
SECRET_KEY=dev-secret-key
GITHUB_CLIENT_SECRET=your-github-secret
```

### Production

Use environment variables or secrets manager:

```bash
# Docker
docker run -e SECRET_KEY=$SECRET_KEY myapp

# Kubernetes Secret
kubectl create secret generic pydotorg-secrets \
  --from-literal=SECRET_KEY=production-secret

# AWS Secrets Manager, HashiCorp Vault, etc.
```

## Validation

Settings are validated on application startup:

```python
from pydotorg.config import settings

# This will raise if required settings are missing
try:
    app = create_app(settings)
except ValidationError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(1)
```

### Custom Validators

```python
from pydantic import field_validator

class Settings(BaseSettings):
    database_url: str

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("Only PostgreSQL is supported")
        return v
```

## Configuration Best Practices

1. **Never commit secrets** - Use `.env` files locally, environment variables in production

2. **Use strong defaults** - Provide sensible defaults for non-secret settings

3. **Validate early** - Validate all settings on startup

4. **Document settings** - Keep this guide updated with all available settings

5. **Use environment-specific files** - Separate configs for dev, test, staging, production

6. **Rotate secrets** - Regularly rotate secret keys and API tokens

7. **Use secret managers** - In production, use a proper secrets management solution

## Generating Secret Keys

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## See Also

- [Feature Flags Guide](feature-flags.md) - Feature flag configuration
- [Deployment Guide](deployment.md) - Production configuration

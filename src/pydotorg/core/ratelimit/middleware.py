r"""Rate limiting middleware configuration using Redis.

This module configures rate limiting for the application using Litestar's built-in
RateLimitConfig with Redis as the backend store. The middleware enforces per-IP
rate limits while excluding health checks, static assets, and API documentation.

Configuration:
    Rate limits are applied per client IP address. Excluded routes:

    - /health (health check endpoint)
    - /static/\* (static files)
    - /schema (OpenAPI schema)
    - /docs (API documentation)
    - /api (OpenAPI endpoint)

Usage::

    from pydotorg.core.ratelimit.middleware import create_rate_limit_config
    from pydotorg.config import settings
    from litestar.stores.redis import RedisStore

    rate_limit_config = create_rate_limit_config(settings)
    redis_store = RedisStore.with_client(url=settings.redis_url)

    app = Litestar(
        middleware=[rate_limit_config.middleware],
        stores={"rate_limit": redis_store},
        ...
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.config.response_cache import ResponseCacheConfig
from litestar.middleware.rate_limit import RateLimitConfig

if TYPE_CHECKING:
    from pydotorg.config import Settings


def create_rate_limit_config(settings: Settings) -> RateLimitConfig:
    """Create rate limiting configuration using Redis as the backend store.

    Configures per-IP rate limiting with:

    - Redis-based persistent storage for distributed rate limiting
    - Automatic rate limit headers (``X-Rate-Limit-*``, ``Retry-After``)
    - Exclusion of health checks, static files, and API documentation
    - 100 requests per minute per IP (default)

    Note:
        The Redis store must be configured in the Litestar app's ``stores`` parameter::

            from litestar.stores.redis import RedisStore
            redis_store = RedisStore.with_client(url=settings.redis_url)
            app = Litestar(stores={"rate_limit": redis_store}, ...)

    Args:
        settings: Application settings containing Redis connection URL

    Returns:
        RateLimitConfig: Configured rate limit middleware instance

    Example:
        >>> from pydotorg.config import settings
        >>> rate_limit_config = create_rate_limit_config(settings)
        >>> rate_limit_config.rate_limit  # ("minute", 100)
    """
    return RateLimitConfig(
        rate_limit=("minute", 100),
        store="rate_limit",
        exclude=[
            "/health",
            "/static/*",
            "/schema",
            "/docs",
            "/api",
        ],
    )


def create_response_cache_config(settings: Settings) -> ResponseCacheConfig:
    """Create response cache configuration using Redis as the backend store.

    Configures response caching with Redis for improved performance. This is
    separate from rate limiting but uses the same Redis instance.

    Note:
        The Redis store must be configured in the Litestar app's `stores` parameter:

        >>> from litestar.stores.redis import RedisStore
        >>> redis_store = RedisStore.with_client(url=settings.redis_url)
        >>> app = Litestar(stores={"response_cache": redis_store}, ...)

    Args:
        settings: Application settings containing Redis connection URL

    Returns:
        ResponseCacheConfig: Configured response cache instance

    Example:
        >>> cache_config = create_response_cache_config(settings)
        >>> cache_config.default_expiration  # 60
    """
    return ResponseCacheConfig(
        default_expiration=60,
        store="response_cache",
    )

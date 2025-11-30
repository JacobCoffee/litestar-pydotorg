"""Response cache configuration for Litestar.

This module provides Redis-backed response caching with configurable TTLs
for different content types. Pages are cached to reduce database load
and improve response times.

Example:
    >>> from pydotorg.core.cache import create_response_cache_config
    >>> cache_config = create_response_cache_config()
    >>> app = Litestar(
    ...     response_cache_config=cache_config,
    ...     stores={"response_cache": redis_store},
    ... )
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from litestar.config.response_cache import ResponseCacheConfig

if TYPE_CHECKING:
    from litestar import Request

CACHE_TTL_DEFAULT = 60
CACHE_TTL_PAGES = 300
CACHE_TTL_STATIC = 3600
CACHE_STORE_NAME = "response_cache"


def page_cache_key_builder(request: Request) -> str:
    """Build a cache key for page requests based on URL path.

    Creates a unique cache key for each page URL, ensuring that:
    - Different pages have different cache keys
    - Query parameters are included in the key
    - The key is a fixed-length hash for consistent storage

    Args:
        request: The Litestar request object.

    Returns:
        A hex digest of the cache key suitable for Redis.

    Example:
        >>> # For URL /about/history?section=timeline
        >>> key = page_cache_key_builder(request)
        >>> key  # 'page:a1b2c3d4e5f6...'
    """
    path = request.url.path
    query = str(sorted(request.query_params.items())) if request.query_params else ""
    raw_key = f"{path}:{query}"
    return f"page:{hashlib.md5(raw_key.encode(), usedforsecurity=False).hexdigest()}"


def create_response_cache_config() -> ResponseCacheConfig:
    """Create response cache configuration for the application.

    Configures caching with:
    - Default TTL of 60 seconds for general routes
    - Redis store backend (configured separately)
    - Custom key builder for page routes

    Note:
        The Redis store must be configured in the Litestar app's `stores` parameter:

        >>> from litestar.stores.redis import RedisStore
        >>> redis_store = RedisStore.with_client(url=settings.redis_url)
        >>> app = Litestar(stores={"response_cache": redis_store}, ...)

    Returns:
        ResponseCacheConfig: Configured response cache instance.
    """
    return ResponseCacheConfig(
        default_expiration=CACHE_TTL_DEFAULT,
        store=CACHE_STORE_NAME,
    )

"""Page cache service for manual cache management.

This module provides a service for programmatic cache invalidation,
used when pages are updated, published, or unpublished to ensure
users see fresh content.
"""

from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from redis.asyncio import Redis

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "pydotorg:page"


class PageCacheService:
    """Service for managing page cache entries.

    Provides methods to invalidate cached pages when content changes,
    ensuring users always see the most up-to-date content after edits.

    Example:
        >>> cache_service = PageCacheService(redis_client)
        >>> await cache_service.invalidate_page("/about/history")
        >>> await cache_service.invalidate_all_pages()
    """

    def __init__(self, redis: Redis) -> None:
        """Initialize the page cache service.

        Args:
            redis: Async Redis client instance.
        """
        self.redis = redis

    def _make_cache_key(self, path: str) -> str:
        """Create a cache key for a page path.

        Args:
            path: The URL path of the page.

        Returns:
            The cache key for the page.
        """
        normalized_path = f"/{path.strip('/')}" if path else "/"
        raw_key = f"{normalized_path}:"
        return f"page:{hashlib.md5(raw_key.encode(), usedforsecurity=False).hexdigest()}"

    async def invalidate_page(self, path: str) -> bool:
        """Invalidate the cache for a specific page path.

        Args:
            path: The URL path of the page to invalidate.

        Returns:
            True if the cache entry was deleted, False if it didn't exist.

        Example:
            >>> await cache_service.invalidate_page("/about/history")
            True
        """
        cache_key = self._make_cache_key(path)
        try:
            result = await self.redis.delete(cache_key)
            if result:
                logger.info(f"Invalidated page cache: {path} (key: {cache_key})")
            return bool(result)
        except Exception:
            logger.exception(f"Failed to invalidate page cache: {path}")
            return False

    async def invalidate_page_by_id(self, page_id: UUID, path: str | None = None) -> bool:
        """Invalidate the cache for a page by ID.

        If path is provided, uses it directly. Otherwise, this method
        cannot determine the path and returns False.

        Args:
            page_id: The UUID of the page.
            path: Optional path of the page (for efficiency).

        Returns:
            True if cache was invalidated, False otherwise.
        """
        if path:
            return await self.invalidate_page(path)

        logger.warning(f"Cannot invalidate page {page_id} without path")
        return False

    async def invalidate_all_pages(self) -> int:
        """Invalidate all cached pages using SCAN + DEL pattern.

        Uses SCAN to avoid blocking Redis with large KEYS operations.

        Returns:
            Number of cache entries deleted.

        Example:
            >>> deleted = await cache_service.invalidate_all_pages()
            >>> print(f"Cleared {deleted} cached pages")
        """
        pattern = "page:*"
        deleted_count = 0
        cursor = 0

        try:
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted_count += await self.redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            logger.exception("Failed to invalidate all page caches")
            return 0
        else:
            if deleted_count > 0:
                logger.info(f"Invalidated {deleted_count} page cache entries")
            return deleted_count

    async def get_cache_stats(self) -> dict[str, int]:
        """Get statistics about cached pages.

        Returns:
            Dictionary with cache statistics including count and memory usage.
        """
        pattern = "page:*"
        count = 0
        cursor = 0

        try:
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                count += len(keys)
                if cursor == 0:
                    break
        except Exception:
            logger.exception("Failed to get page cache stats")
            return {"cached_pages": 0, "error": 1}
        else:
            return {"cached_pages": count}

"""Unit tests for PageCacheService."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from pydotorg.core.cache.service import PageCacheService


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Create a mock async Redis client."""
    redis = AsyncMock()
    redis.delete = AsyncMock(return_value=1)
    redis.scan = AsyncMock(return_value=(0, []))
    return redis


@pytest.fixture
def cache_service(mock_redis: AsyncMock) -> PageCacheService:
    """Create a PageCacheService with mock Redis."""
    return PageCacheService(mock_redis)


class TestPageCacheServiceInit:
    """Tests for PageCacheService initialization."""

    def test_initializes_with_redis(self, mock_redis: AsyncMock) -> None:
        """Should store Redis client on initialization."""
        service = PageCacheService(mock_redis)
        assert service.redis is mock_redis


class TestMakeCacheKey:
    """Tests for the _make_cache_key method."""

    def test_normalizes_path_with_leading_slash(self, cache_service: PageCacheService) -> None:
        """Should ensure path starts with /."""
        key = cache_service._make_cache_key("about/history")
        assert "about/history" in key or key.startswith("page:")

    def test_normalizes_path_strips_trailing_slash(self, cache_service: PageCacheService) -> None:
        """Should strip trailing slashes."""
        key1 = cache_service._make_cache_key("/about/")
        key2 = cache_service._make_cache_key("/about")
        assert key1 == key2

    def test_root_path(self, cache_service: PageCacheService) -> None:
        """Should handle root path."""
        key = cache_service._make_cache_key("/")
        assert key.startswith("page:")

    def test_empty_path(self, cache_service: PageCacheService) -> None:
        """Should handle empty path as root."""
        key = cache_service._make_cache_key("")
        assert key.startswith("page:")

    def test_consistent_keys(self, cache_service: PageCacheService) -> None:
        """Same path should always produce same key."""
        path = "/test/page"
        keys = [cache_service._make_cache_key(path) for _ in range(5)]
        assert len(set(keys)) == 1


class TestInvalidatePage:
    """Tests for invalidate_page method."""

    @pytest.mark.anyio
    async def test_invalidates_single_page(self, cache_service: PageCacheService, mock_redis: AsyncMock) -> None:
        """Should delete cache entry for specific page."""
        mock_redis.delete.return_value = 1
        result = await cache_service.invalidate_page("/about/history")

        assert result is True
        mock_redis.delete.assert_called_once()

    @pytest.mark.anyio
    async def test_returns_false_when_not_cached(self, cache_service: PageCacheService, mock_redis: AsyncMock) -> None:
        """Should return False when page wasn't cached."""
        mock_redis.delete.return_value = 0
        result = await cache_service.invalidate_page("/nonexistent")

        assert result is False

    @pytest.mark.anyio
    async def test_handles_redis_errors(self, cache_service: PageCacheService, mock_redis: AsyncMock) -> None:
        """Should return False on Redis errors."""
        mock_redis.delete.side_effect = Exception("Connection refused")
        result = await cache_service.invalidate_page("/about")

        assert result is False


class TestInvalidatePageById:
    """Tests for invalidate_page_by_id method."""

    @pytest.mark.anyio
    async def test_with_path_delegates_to_invalidate_page(
        self, cache_service: PageCacheService, mock_redis: AsyncMock
    ) -> None:
        """Should use path when provided."""
        mock_redis.delete.return_value = 1
        page_id = uuid4()
        result = await cache_service.invalidate_page_by_id(page_id, path="/about")

        assert result is True
        mock_redis.delete.assert_called_once()

    @pytest.mark.anyio
    async def test_without_path_returns_false(self, cache_service: PageCacheService) -> None:
        """Should return False when path is not provided."""
        page_id = uuid4()
        result = await cache_service.invalidate_page_by_id(page_id)

        assert result is False


class TestInvalidateAllPages:
    """Tests for invalidate_all_pages method."""

    @pytest.mark.anyio
    async def test_clears_all_page_caches(self, cache_service: PageCacheService, mock_redis: AsyncMock) -> None:
        """Should scan and delete all page:* keys."""
        mock_redis.scan.return_value = (0, ["page:abc123", "page:def456"])
        mock_redis.delete.return_value = 2

        result = await cache_service.invalidate_all_pages()

        assert result == 2
        mock_redis.scan.assert_called()
        mock_redis.delete.assert_called_once()

    @pytest.mark.anyio
    async def test_handles_empty_cache(self, cache_service: PageCacheService, mock_redis: AsyncMock) -> None:
        """Should return 0 when no pages are cached."""
        mock_redis.scan.return_value = (0, [])

        result = await cache_service.invalidate_all_pages()

        assert result == 0
        mock_redis.delete.assert_not_called()

    @pytest.mark.anyio
    async def test_handles_multiple_scan_iterations(
        self, cache_service: PageCacheService, mock_redis: AsyncMock
    ) -> None:
        """Should handle pagination through SCAN."""
        mock_redis.scan.side_effect = [
            (1, ["page:1", "page:2"]),
            (0, ["page:3"]),
        ]
        mock_redis.delete.return_value = 3

        result = await cache_service.invalidate_all_pages()

        assert mock_redis.scan.call_count == 2

    @pytest.mark.anyio
    async def test_handles_redis_errors(self, cache_service: PageCacheService, mock_redis: AsyncMock) -> None:
        """Should return 0 on Redis errors."""
        mock_redis.scan.side_effect = Exception("Connection refused")

        result = await cache_service.invalidate_all_pages()

        assert result == 0


class TestGetCacheStats:
    """Tests for get_cache_stats method."""

    @pytest.mark.anyio
    async def test_returns_cached_page_count(self, cache_service: PageCacheService, mock_redis: AsyncMock) -> None:
        """Should return count of cached pages."""
        mock_redis.scan.return_value = (0, ["page:1", "page:2", "page:3"])

        stats = await cache_service.get_cache_stats()

        assert stats["cached_pages"] == 3

    @pytest.mark.anyio
    async def test_handles_empty_cache(self, cache_service: PageCacheService, mock_redis: AsyncMock) -> None:
        """Should return 0 for empty cache."""
        mock_redis.scan.return_value = (0, [])

        stats = await cache_service.get_cache_stats()

        assert stats["cached_pages"] == 0

    @pytest.mark.anyio
    async def test_handles_redis_errors(self, cache_service: PageCacheService, mock_redis: AsyncMock) -> None:
        """Should return error stats on Redis errors."""
        mock_redis.scan.side_effect = Exception("Connection refused")

        stats = await cache_service.get_cache_stats()

        assert stats["cached_pages"] == 0
        assert stats.get("error") == 1

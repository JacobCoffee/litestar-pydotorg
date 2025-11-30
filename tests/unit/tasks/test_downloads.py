"""Unit tests for download statistics tracking service and tasks."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pydotorg.tasks.downloads import (
    DownloadStatsService,
    aggregate_download_stats,
    flush_download_stats,
    get_download_stats_service,
)

if TYPE_CHECKING:
    pass


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Mock Redis client for testing."""
    redis = AsyncMock()
    redis.incr = AsyncMock(return_value=1)
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock(return_value=1)
    redis.scan_iter = MagicMock(return_value=AsyncIteratorMock([]))
    return redis


class AsyncIteratorMock:
    """Async iterator mock for Redis scan_iter."""

    def __init__(self, items: list[Any]) -> None:
        self.items = items
        self.index = 0

    def __aiter__(self) -> AsyncIteratorMock:
        return self

    async def __anext__(self) -> Any:
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


class TestDownloadStatsService:
    """Tests for DownloadStatsService class."""

    def test_init(self, mock_redis: AsyncMock) -> None:
        service = DownloadStatsService(mock_redis)
        assert service.redis is mock_redis
        assert service.namespace == "pydotorg"

    def test_init_custom_namespace(self, mock_redis: AsyncMock) -> None:
        service = DownloadStatsService(mock_redis, namespace="custom")
        assert service.namespace == "custom"

    def test_key_building(self, mock_redis: AsyncMock) -> None:
        service = DownloadStatsService(mock_redis)
        key = service._key("file", "123", "total")
        assert key == "pydotorg:downloads:stats:file:123:total"

    def test_key_building_custom_namespace(self, mock_redis: AsyncMock) -> None:
        service = DownloadStatsService(mock_redis, namespace="test")
        key = service._key("file", "123", "total")
        assert key == "test:downloads:stats:file:123:total"

    @pytest.mark.anyio
    async def test_track_download(self, mock_redis: AsyncMock) -> None:
        service = DownloadStatsService(mock_redis)
        await service.track_download("file-123")

        assert mock_redis.incr.call_count == 4
        calls = [call[0][0] for call in mock_redis.incr.call_args_list]
        assert "pydotorg:downloads:stats:file:file-123:total" in calls
        assert "pydotorg:downloads:stats:total:all" in calls

    @pytest.mark.anyio
    async def test_track_download_with_release(self, mock_redis: AsyncMock) -> None:
        service = DownloadStatsService(mock_redis)
        await service.track_download("file-123", release_id="release-456")

        assert mock_redis.incr.call_count == 6
        calls = [call[0][0] for call in mock_redis.incr.call_args_list]
        assert "pydotorg:downloads:stats:release:release-456:total" in calls

    @pytest.mark.anyio
    async def test_track_download_redis_error(self, mock_redis: AsyncMock) -> None:
        mock_redis.incr.side_effect = Exception("Redis connection error")
        service = DownloadStatsService(mock_redis)
        await service.track_download("file-123")

    @pytest.mark.anyio
    async def test_get_file_downloads(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = b"42"
        service = DownloadStatsService(mock_redis)
        count = await service.get_file_downloads("file-123")
        assert count == 42
        mock_redis.get.assert_called_once_with("pydotorg:downloads:stats:file:file-123:total")

    @pytest.mark.anyio
    async def test_get_file_downloads_no_data(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = None
        service = DownloadStatsService(mock_redis)
        count = await service.get_file_downloads("file-123")
        assert count == 0

    @pytest.mark.anyio
    async def test_get_file_downloads_error(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.side_effect = Exception("Error")
        service = DownloadStatsService(mock_redis)
        count = await service.get_file_downloads("file-123")
        assert count == 0

    @pytest.mark.anyio
    async def test_get_file_downloads_daily(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = b"10"
        service = DownloadStatsService(mock_redis)
        today = date.today()
        count = await service.get_file_downloads_daily("file-123", today)
        assert count == 10
        expected_key = f"pydotorg:downloads:stats:file:file-123:daily:{today.isoformat()}"
        mock_redis.get.assert_called_once_with(expected_key)

    @pytest.mark.anyio
    async def test_get_file_downloads_daily_default_today(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = b"5"
        service = DownloadStatsService(mock_redis)
        count = await service.get_file_downloads_daily("file-123")
        assert count == 5

    @pytest.mark.anyio
    async def test_get_release_downloads(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = b"100"
        service = DownloadStatsService(mock_redis)
        count = await service.get_release_downloads("release-456")
        assert count == 100
        mock_redis.get.assert_called_once_with("pydotorg:downloads:stats:release:release-456:total")

    @pytest.mark.anyio
    async def test_get_total_downloads(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = b"1000"
        service = DownloadStatsService(mock_redis)
        count = await service.get_total_downloads()
        assert count == 1000
        mock_redis.get.assert_called_once_with("pydotorg:downloads:stats:total:all")

    @pytest.mark.anyio
    async def test_get_daily_downloads(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = b"50"
        service = DownloadStatsService(mock_redis)
        today = date.today()
        count = await service.get_daily_downloads(today)
        assert count == 50
        expected_key = f"pydotorg:downloads:stats:daily:{today.isoformat()}"
        mock_redis.get.assert_called_once_with(expected_key)

    @pytest.mark.anyio
    async def test_get_top_downloads(self, mock_redis: AsyncMock) -> None:
        mock_redis.scan_iter = MagicMock(
            return_value=AsyncIteratorMock(
                [
                    b"pydotorg:downloads:stats:file:abc:total",
                    b"pydotorg:downloads:stats:file:def:total",
                ]
            )
        )
        mock_redis.get = AsyncMock(side_effect=[b"100", b"50"])

        service = DownloadStatsService(mock_redis)
        top = await service.get_top_downloads(limit=5)

        assert len(top) == 2
        assert top[0] == ("abc", 100)
        assert top[1] == ("def", 50)

    @pytest.mark.anyio
    async def test_get_top_downloads_empty(self, mock_redis: AsyncMock) -> None:
        mock_redis.scan_iter = MagicMock(return_value=AsyncIteratorMock([]))
        service = DownloadStatsService(mock_redis)
        top = await service.get_top_downloads()
        assert top == []

    @pytest.mark.anyio
    async def test_get_all_file_stats(self, mock_redis: AsyncMock) -> None:
        mock_redis.scan_iter = MagicMock(
            return_value=AsyncIteratorMock(
                [
                    b"pydotorg:downloads:stats:file:xyz:total",
                ]
            )
        )
        mock_redis.get = AsyncMock(return_value=b"75")

        service = DownloadStatsService(mock_redis)
        stats = await service.get_all_file_stats()

        assert stats == {"xyz": 75}

    @pytest.mark.anyio
    async def test_get_stats_summary(self, mock_redis: AsyncMock) -> None:
        mock_redis.get = AsyncMock(return_value=b"500")
        mock_redis.scan_iter = MagicMock(return_value=AsyncIteratorMock([]))

        service = DownloadStatsService(mock_redis)
        summary = await service.get_stats_summary()

        assert summary["total_downloads"] == 500
        assert summary["downloads_today"] == 500
        assert "last_updated" in summary
        assert summary["top_files"] == []

    @pytest.mark.anyio
    async def test_cleanup_old_daily_keys(self, mock_redis: AsyncMock) -> None:
        old_date = (date.today() - timedelta(days=10)).isoformat()
        mock_redis.scan_iter = MagicMock(
            return_value=AsyncIteratorMock(
                [
                    f"pydotorg:downloads:stats:file:abc:daily:{old_date}".encode(),
                ]
            )
        )
        mock_redis.delete = AsyncMock(return_value=1)

        service = DownloadStatsService(mock_redis)
        deleted = await service.cleanup_old_daily_keys(days_to_keep=7)

        assert deleted == 1
        mock_redis.delete.assert_called_once()

    @pytest.mark.anyio
    async def test_cleanup_old_daily_keys_keeps_recent(self, mock_redis: AsyncMock) -> None:
        recent_date = (date.today() - timedelta(days=2)).isoformat()
        mock_redis.scan_iter = MagicMock(
            return_value=AsyncIteratorMock(
                [
                    f"pydotorg:downloads:stats:file:abc:daily:{recent_date}".encode(),
                ]
            )
        )

        service = DownloadStatsService(mock_redis)
        deleted = await service.cleanup_old_daily_keys(days_to_keep=7)

        assert deleted == 0
        mock_redis.delete.assert_not_called()


class TestGetDownloadStatsService:
    """Tests for get_download_stats_service function."""

    @pytest.mark.anyio
    async def test_creates_service_when_redis_available(self) -> None:
        redis = AsyncMock()
        ctx: dict[str, Any] = {"redis": redis}

        with patch("pydotorg.config.settings") as mock_settings:
            mock_settings.redis_stats_namespace = "test_ns"
            service = await get_download_stats_service(ctx)

        assert service is not None
        assert "download_stats_service" in ctx

    @pytest.mark.anyio
    async def test_returns_existing_service(self) -> None:
        redis = AsyncMock()
        existing_service = DownloadStatsService(redis)
        ctx: dict[str, Any] = {"redis": redis, "download_stats_service": existing_service}

        service = await get_download_stats_service(ctx)

        assert service is existing_service

    @pytest.mark.anyio
    async def test_returns_none_when_no_redis(self) -> None:
        ctx: dict[str, Any] = {}
        service = await get_download_stats_service(ctx)
        assert service is None


class TestFlushDownloadStatsTask:
    """Tests for flush_download_stats SAQ task."""

    @pytest.mark.anyio
    async def test_returns_error_when_no_stats_service(self) -> None:
        ctx: dict[str, Any] = {}
        result = await flush_download_stats(ctx)
        assert result["success"] is False
        assert "Stats service unavailable" in result["error"]

    @pytest.mark.anyio
    async def test_returns_error_when_no_session(self) -> None:
        redis = AsyncMock()
        ctx: dict[str, Any] = {"redis": redis}

        result = await flush_download_stats(ctx)

        assert result["success"] is False
        assert "Database session unavailable" in result["error"]

    @pytest.mark.anyio
    async def test_successful_flush(self) -> None:
        redis = AsyncMock()
        redis.scan_iter = MagicMock(return_value=AsyncIteratorMock([]))
        session = AsyncMock()

        ctx: dict[str, Any] = {"redis": redis, "db_session": session}

        result = await flush_download_stats(ctx)

        assert result["success"] is True
        assert "flushed" in result
        assert "cleaned_keys" in result


class TestAggregateDownloadStatsTask:
    """Tests for aggregate_download_stats SAQ task."""

    @pytest.mark.anyio
    async def test_returns_error_when_no_stats_service(self) -> None:
        ctx: dict[str, Any] = {}
        result = await aggregate_download_stats(ctx)
        assert result["success"] is False
        assert "Stats service unavailable" in result["error"]

    @pytest.mark.anyio
    async def test_successful_aggregation(self) -> None:
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=b"100")
        redis.scan_iter = MagicMock(return_value=AsyncIteratorMock([]))

        ctx: dict[str, Any] = {"redis": redis}

        result = await aggregate_download_stats(ctx)

        assert result["success"] is True
        assert "summary" in result
        assert result["summary"]["total_downloads"] == 100

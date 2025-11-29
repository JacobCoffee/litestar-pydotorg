"""Tests for persistent task statistics tracking."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

if TYPE_CHECKING:
    from pydotorg.tasks.stats import TaskStatsService


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Create a mock Redis client with expected methods."""
    redis = AsyncMock()
    redis.incr = AsyncMock(return_value=1)
    redis.get = AsyncMock(return_value=None)
    redis.scan_iter = AsyncMock(return_value=[])
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def stats_service(mock_redis: AsyncMock) -> TaskStatsService:
    """Create stats service with mocked Redis."""
    from pydotorg.tasks.stats import TaskStatsService

    return TaskStatsService(mock_redis, namespace="test")


async def test_increment_complete(stats_service: TaskStatsService, mock_redis: AsyncMock) -> None:
    """Test incrementing complete counter."""
    await stats_service.increment_complete()
    mock_redis.incr.assert_awaited_once_with("test:tasks:stats:total:complete")


async def test_increment_complete_with_function(stats_service: TaskStatsService, mock_redis: AsyncMock) -> None:
    """Test incrementing complete counter for specific function."""
    await stats_service.increment_complete("send_email")
    assert mock_redis.incr.await_count == 2
    mock_redis.incr.assert_any_await("test:tasks:stats:total:complete")
    mock_redis.incr.assert_any_await("test:tasks:stats:func:send_email:complete")


async def test_increment_failed(stats_service: TaskStatsService, mock_redis: AsyncMock) -> None:
    """Test incrementing failed counter."""
    await stats_service.increment_failed()
    mock_redis.incr.assert_awaited_once_with("test:tasks:stats:total:failed")


async def test_increment_failed_with_function(stats_service: TaskStatsService, mock_redis: AsyncMock) -> None:
    """Test incrementing failed counter for specific function."""
    await stats_service.increment_failed("process_data")
    assert mock_redis.incr.await_count == 2
    mock_redis.incr.assert_any_await("test:tasks:stats:total:failed")
    mock_redis.incr.assert_any_await("test:tasks:stats:func:process_data:failed")


async def test_increment_retried(stats_service: TaskStatsService, mock_redis: AsyncMock) -> None:
    """Test incrementing retried counter."""
    await stats_service.increment_retried()
    mock_redis.incr.assert_awaited_once_with("test:tasks:stats:total:retried")


async def test_get_stats(stats_service: TaskStatsService, mock_redis: AsyncMock) -> None:
    """Test retrieving total statistics."""
    mock_redis.get = AsyncMock(side_effect=["10", "5", "2"])

    stats = await stats_service.get_stats()

    assert stats == {"complete": 10, "failed": 5, "retried": 2}
    assert mock_redis.get.await_count == 3


async def test_get_stats_missing_values(stats_service: TaskStatsService, mock_redis: AsyncMock) -> None:
    """Test getting stats when some values don't exist."""
    mock_redis.get = AsyncMock(side_effect=[None, "3", None])

    stats = await stats_service.get_stats()

    assert stats == {"complete": 0, "failed": 3, "retried": 0}


async def test_get_function_stats(stats_service: TaskStatsService, mock_redis: AsyncMock) -> None:
    """Test retrieving function-specific statistics."""
    mock_redis.get = AsyncMock(side_effect=["5", "1", "0"])

    stats = await stats_service.get_function_stats("send_email")

    assert stats == {"complete": 5, "failed": 1, "retried": 0}


async def test_key_namespace(stats_service: TaskStatsService) -> None:
    """Test that keys are properly namespaced."""
    key = stats_service._key("total", "complete")
    assert key == "test:tasks:stats:total:complete"

    key = stats_service._key("func", "my_task", "failed")
    assert key == "test:tasks:stats:func:my_task:failed"


async def test_increment_handles_redis_error(stats_service: TaskStatsService, mock_redis: AsyncMock) -> None:
    """Test graceful handling of Redis errors during increment."""
    mock_redis.incr = AsyncMock(side_effect=Exception("Redis connection lost"))

    await stats_service.increment_complete("test_func")


async def test_get_stats_handles_redis_error(stats_service: TaskStatsService, mock_redis: AsyncMock) -> None:
    """Test graceful handling of Redis errors during get."""
    mock_redis.get = AsyncMock(side_effect=Exception("Redis connection lost"))

    stats = await stats_service.get_stats()

    assert stats == {"complete": 0, "failed": 0, "retried": 0}


async def test_get_stats_service_from_context() -> None:
    """Test getting stats service from worker context."""
    from pydotorg.tasks.stats import get_stats_service

    mock_redis = AsyncMock()
    ctx: dict = {"redis": mock_redis}

    service1 = await get_stats_service(ctx)
    assert service1 is not None
    assert "stats_service" in ctx

    service2 = await get_stats_service(ctx)
    assert service2 is service1


async def test_get_stats_service_no_redis() -> None:
    """Test graceful handling when Redis is unavailable."""
    from pydotorg.tasks.stats import get_stats_service

    ctx: dict = {}
    service = await get_stats_service(ctx)
    assert service is None


async def test_reset_stats(stats_service: TaskStatsService, mock_redis: AsyncMock) -> None:
    """Test resetting all statistics."""
    keys = [
        b"test:tasks:stats:total:complete",
        b"test:tasks:stats:total:failed",
        b"test:tasks:stats:func:task1:complete",
    ]

    async def mock_scan_iter(match: str):
        for key in keys:
            yield key

    mock_redis.scan_iter = mock_scan_iter
    mock_redis.delete = AsyncMock()

    await stats_service.reset_stats()

    assert mock_redis.delete.await_count == len(keys)

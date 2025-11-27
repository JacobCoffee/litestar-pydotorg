"""Tests for cache warming tasks."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from pydotorg.tasks.cache import (
    CACHE_KEY_PREFIX,
    clear_cache,
    get_cache_stats,
    warm_blogs_cache,
    warm_events_cache,
    warm_homepage_cache,
    warm_pages_cache,
    warm_releases_cache,
)

if TYPE_CHECKING:
    pass


@pytest.fixture
def mock_context() -> dict:
    """Create a mock SAQ context with session_maker."""
    redis_mock = AsyncMock()
    redis_mock.set = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.scan = AsyncMock(return_value=(0, []))
    redis_mock.delete = AsyncMock()
    redis_mock.info = AsyncMock(
        return_value={
            "keyspace_hits": 1000,
            "keyspace_misses": 100,
            "used_memory_human": "10M",
            "used_memory_peak_human": "15M",
        }
    )

    session_mock = AsyncMock()
    session_maker_mock = MagicMock()
    session_maker_mock.return_value.__aenter__ = AsyncMock(return_value=session_mock)
    session_maker_mock.return_value.__aexit__ = AsyncMock(return_value=None)

    return {
        "redis": redis_mock,
        "session_maker": session_maker_mock,
    }


@pytest.mark.asyncio
async def test_warm_homepage_cache(mock_context: dict) -> None:
    """Test homepage cache warming."""
    blog_entry = MagicMock()
    blog_entry.id = uuid4()
    blog_entry.title = "Test Blog"
    blog_entry.summary = "Summary"
    blog_entry.url = "https://blog.python.org/test"
    blog_entry.pub_date = datetime.now(tz=UTC)

    event = MagicMock()
    event.id = uuid4()
    event.name = "Test Event"
    event.title = "Event Title"
    event.description = "Description"
    event.featured = True

    release = MagicMock()
    release.id = uuid4()
    release.name = "Python 3.12.0"
    release.slug = "python-3-12-0"
    release.version = "3.12.0"
    release.is_latest = True
    release.release_date = datetime.now(tz=UTC).date()

    with (
        patch("pydotorg.tasks.cache.BlogEntryService") as blog_service_mock,
        patch("pydotorg.tasks.cache.EventService") as event_service_mock,
        patch("pydotorg.tasks.cache.ReleaseService") as release_service_mock,
    ):
        blog_instance = blog_service_mock.return_value
        blog_instance.get_recent_entries = AsyncMock(return_value=[blog_entry])

        event_instance = event_service_mock.return_value
        event_instance.get_upcoming = AsyncMock(return_value=[event])

        release_instance = release_service_mock.return_value
        release_instance.get_latest = AsyncMock(return_value=release)

        result = await warm_homepage_cache(mock_context)

        assert result["cached"] == 3
        assert result["errors"] == 0
        assert mock_context["redis"].set.call_count == 3


@pytest.mark.asyncio
async def test_warm_releases_cache(mock_context: dict) -> None:
    """Test releases cache warming."""
    release = MagicMock()
    release.id = uuid4()
    release.name = "Python 3.12.0"
    release.slug = "python-3-12-0"
    release.version = "3.12.0"
    release.is_latest = True
    release.release_date = datetime.now(tz=UTC).date()
    release.release_page = "https://python.org/downloads/release/3-12-0"

    with patch("pydotorg.tasks.cache.ReleaseService") as release_service_mock:
        release_instance = release_service_mock.return_value
        release_instance.get_latest = AsyncMock(return_value=release)
        release_instance.get_published = AsyncMock(return_value=[release])
        release_instance.get_for_download_page = AsyncMock(return_value=[release])

        result = await warm_releases_cache(mock_context)

        assert result["cached"] == 3
        assert result["errors"] == 0
        assert mock_context["redis"].set.call_count == 3


@pytest.mark.asyncio
async def test_warm_events_cache(mock_context: dict) -> None:
    """Test events cache warming."""
    event = MagicMock()
    event.id = uuid4()
    event.name = "Test Event"
    event.slug = "test-event"
    event.title = "Event Title"
    event.description = "Description"
    event.featured = True

    with patch("pydotorg.tasks.cache.EventService") as event_service_mock:
        event_instance = event_service_mock.return_value
        event_instance.get_upcoming = AsyncMock(return_value=[event])
        event_instance.get_featured = AsyncMock(return_value=[event])

        result = await warm_events_cache(mock_context)

        assert result["cached"] == 2
        assert result["errors"] == 0
        assert mock_context["redis"].set.call_count == 2


@pytest.mark.asyncio
async def test_warm_blogs_cache(mock_context: dict) -> None:
    """Test blogs cache warming."""
    blog_entry = MagicMock()
    blog_entry.id = uuid4()
    blog_entry.title = "Test Blog"
    blog_entry.summary = "Summary"
    blog_entry.url = "https://blog.python.org/test"
    blog_entry.pub_date = datetime.now(tz=UTC)
    blog_entry.feed_id = uuid4()

    with patch("pydotorg.tasks.cache.BlogEntryService") as blog_service_mock:
        blog_instance = blog_service_mock.return_value
        blog_instance.get_recent_entries = AsyncMock(return_value=[blog_entry])

        result = await warm_blogs_cache(mock_context)

        assert result["cached"] == 1
        assert result["errors"] == 0
        assert mock_context["redis"].set.call_count == 1


@pytest.mark.asyncio
async def test_warm_pages_cache(mock_context: dict) -> None:
    """Test pages cache warming."""
    page = MagicMock()
    page.id = uuid4()
    page.title = "Homepage"
    page.path = "/"
    page.content = "Welcome to Python.org"
    page.content_type = MagicMock()
    page.content_type.value = "markdown"
    page.description = "The official home"
    page.is_published = True

    with patch("pydotorg.tasks.cache.PageAdminService") as page_service_mock:
        page_instance = page_service_mock.return_value
        page_instance.get_page_by_path = AsyncMock(return_value=page)

        result = await warm_pages_cache(mock_context)

        assert result["cached"] == 4
        assert result["errors"] == 0
        assert mock_context["redis"].set.call_count == 4


@pytest.mark.asyncio
async def test_warm_pages_cache_custom_paths(mock_context: dict) -> None:
    """Test pages cache warming with custom paths."""
    page = MagicMock()
    page.id = uuid4()
    page.title = "Custom Page"
    page.path = "/custom"
    page.content = "Custom content"
    page.content_type = MagicMock()
    page.content_type.value = "html"
    page.description = "Custom description"
    page.is_published = True

    with patch("pydotorg.tasks.cache.PageAdminService") as page_service_mock:
        page_instance = page_service_mock.return_value
        page_instance.get_page_by_path = AsyncMock(return_value=page)

        result = await warm_pages_cache(mock_context, page_paths=["/custom"])

        assert result["cached"] == 1
        assert result["errors"] == 0


@pytest.mark.asyncio
async def test_clear_cache(mock_context: dict) -> None:
    """Test cache clearing."""
    test_keys = [
        f"{CACHE_KEY_PREFIX}:test1".encode(),
        f"{CACHE_KEY_PREFIX}:test2".encode(),
    ]

    mock_context["redis"].scan = AsyncMock(return_value=(0, test_keys))

    result = await clear_cache(mock_context)

    assert result["cleared"] == 2
    mock_context["redis"].delete.assert_called_once_with(*test_keys)


@pytest.mark.asyncio
async def test_clear_cache_with_pattern(mock_context: dict) -> None:
    """Test cache clearing with pattern."""
    test_keys = [
        f"{CACHE_KEY_PREFIX}:releases:latest".encode(),
    ]

    mock_context["redis"].scan = AsyncMock(return_value=(0, test_keys))

    result = await clear_cache(mock_context, pattern="releases:*")

    assert result["cleared"] == 1


@pytest.mark.asyncio
async def test_get_cache_stats(mock_context: dict) -> None:
    """Test cache statistics retrieval."""
    mock_context["redis"].scan = AsyncMock(
        side_effect=[
            (1, [b"key1", b"key2", f"{CACHE_KEY_PREFIX}:test".encode()]),
            (0, [b"key3", f"{CACHE_KEY_PREFIX}:test2".encode()]),
        ]
    )

    result = await get_cache_stats(mock_context)

    assert result["total_keys"] == 5
    assert result["pydotorg_keys"] == 2
    assert result["keyspace_hits"] == 1000
    assert result["keyspace_misses"] == 100
    assert result["hit_rate"] == 90.91
    assert result["memory_used"] == "10M"
    assert result["memory_peak"] == "15M"


@pytest.mark.asyncio
async def test_warm_homepage_cache_handles_errors(mock_context: dict) -> None:
    """Test homepage cache warming handles errors gracefully."""
    with (
        patch("pydotorg.tasks.cache.BlogEntryService") as blog_service_mock,
        patch("pydotorg.tasks.cache.EventService") as event_service_mock,
        patch("pydotorg.tasks.cache.ReleaseService") as release_service_mock,
    ):
        blog_instance = blog_service_mock.return_value
        blog_instance.get_recent_entries = AsyncMock(side_effect=Exception("DB error"))

        event_instance = event_service_mock.return_value
        event_instance.get_upcoming = AsyncMock(return_value=[])

        release_instance = release_service_mock.return_value
        release_instance.get_latest = AsyncMock(return_value=None)

        result = await warm_homepage_cache(mock_context)

        assert result["errors"] == 1
        assert result["cached"] == 1

"""Unit tests for feed aggregation background tasks."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from pydotorg.domains.blogs.models import Feed


@pytest.fixture
def mock_feeds_ctx(mock_session_maker: AsyncMock) -> dict:
    """Mock SAQ context for feed tasks with session_maker."""
    return {"session_maker": mock_session_maker}


@pytest.mark.unit
class TestRefreshAllFeeds:
    """Test suite for refresh_all_feeds task."""

    async def test_refreshes_all_active_feeds_success(
        self,
        mock_feeds_ctx: dict,
        mock_session_maker: AsyncMock,
        sample_feeds: list[Feed],
        sample_blog_entries: list,
    ) -> None:
        """Test successful refresh of all active feeds."""
        with patch("pydotorg.domains.blogs.services.FeedService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_active_feeds = AsyncMock(return_value=sample_feeds)
            mock_service.fetch_feed = AsyncMock(return_value=sample_blog_entries)

            from pydotorg.tasks.feeds import refresh_all_feeds

            result = await refresh_all_feeds(mock_feeds_ctx)

            assert result["success_count"] == len(sample_feeds)
            assert result["error_count"] == 0
            assert result["total_feeds"] == len(sample_feeds)
            mock_service.get_active_feeds.assert_called_once_with(limit=1000)
            assert mock_service.fetch_feed.call_count == len(sample_feeds)

    async def test_handles_empty_feed_list(self, mock_feeds_ctx: dict, mock_session_maker: AsyncMock) -> None:
        """Test handling when no active feeds exist."""
        with patch("pydotorg.domains.blogs.services.FeedService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_active_feeds = AsyncMock(return_value=[])

            from pydotorg.tasks.feeds import refresh_all_feeds

            result = await refresh_all_feeds(mock_feeds_ctx)

            assert result["success_count"] == 0
            assert result["error_count"] == 0
            assert result["total_feeds"] == 0

    async def test_continues_on_partial_failure(
        self, mock_feeds_ctx: dict, mock_session_maker: AsyncMock, sample_feeds: list[Feed]
    ) -> None:
        """Test that task continues when individual feeds fail."""
        with patch("pydotorg.domains.blogs.services.FeedService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_active_feeds = AsyncMock(return_value=sample_feeds)
            mock_service.fetch_feed = AsyncMock(
                side_effect=[
                    Exception("Parse error"),
                    [],
                    [],
                ]
            )

            from pydotorg.tasks.feeds import refresh_all_feeds

            result = await refresh_all_feeds(mock_feeds_ctx)

            assert result["success_count"] == 2
            assert result["error_count"] == 1
            assert result["total_feeds"] == 3

    async def test_raises_on_critical_failure(self, mock_feeds_ctx: dict, mock_session_maker: AsyncMock) -> None:
        """Test that critical errors are raised."""
        with patch("pydotorg.domains.blogs.services.FeedService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_active_feeds = AsyncMock(side_effect=Exception("Database error"))

            from pydotorg.tasks.feeds import refresh_all_feeds

            with pytest.raises(Exception, match="Database error"):
                await refresh_all_feeds(mock_feeds_ctx)


@pytest.mark.unit
class TestRefreshStaleFeeds:
    """Test suite for refresh_stale_feeds task."""

    async def test_refreshes_stale_feeds_with_cutoff(
        self, mock_feeds_ctx: dict, mock_session_maker: AsyncMock, sample_feeds: list[Feed]
    ) -> None:
        """Test refreshing only stale feeds."""
        stale_feeds = sample_feeds[:2]

        with patch("pydotorg.domains.blogs.services.FeedService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_feeds_needing_update = AsyncMock(return_value=stale_feeds)
            mock_service.fetch_feed = AsyncMock(return_value=[])

            from pydotorg.tasks.feeds import refresh_stale_feeds

            result = await refresh_stale_feeds(mock_feeds_ctx, max_age_hours=1)

            assert result["success_count"] == len(stale_feeds)
            assert result["error_count"] == 0
            assert result["total_feeds"] == len(stale_feeds)
            assert result["max_age_hours"] == 1
            assert "cutoff_time" in result
            mock_service.get_feeds_needing_update.assert_called_once()

    async def test_uses_default_max_age(self, mock_feeds_ctx: dict, mock_session_maker: AsyncMock) -> None:
        """Test default max_age_hours parameter."""
        with patch("pydotorg.domains.blogs.services.FeedService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_feeds_needing_update = AsyncMock(return_value=[])

            from pydotorg.tasks.feeds import refresh_stale_feeds

            result = await refresh_stale_feeds(mock_feeds_ctx)

            assert result["max_age_hours"] == 1

    async def test_handles_partial_failure_stale(
        self, mock_feeds_ctx: dict, mock_session_maker: AsyncMock, sample_feeds: list[Feed]
    ) -> None:
        """Test handling partial failures in stale feed refresh."""
        with patch("pydotorg.domains.blogs.services.FeedService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_feeds_needing_update = AsyncMock(return_value=sample_feeds[:2])
            mock_service.fetch_feed = AsyncMock(side_effect=[Exception("Network error"), []])

            from pydotorg.tasks.feeds import refresh_stale_feeds

            result = await refresh_stale_feeds(mock_feeds_ctx)

            assert result["success_count"] == 1
            assert result["error_count"] == 1


@pytest.mark.unit
class TestRefreshSingleFeed:
    """Test suite for refresh_single_feed task."""

    async def test_refreshes_specific_feed_success(
        self,
        mock_feeds_ctx: dict,
        mock_session_maker: AsyncMock,
        sample_feed: Feed,
        sample_blog_entries: list,
    ) -> None:
        """Test successful single feed refresh."""
        sample_feed.last_fetched = datetime.now(UTC)

        with patch("pydotorg.domains.blogs.services.FeedService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get = AsyncMock(return_value=sample_feed)
            mock_service.fetch_feed = AsyncMock(return_value=sample_blog_entries)

            from pydotorg.tasks.feeds import refresh_single_feed

            result = await refresh_single_feed(mock_feeds_ctx, feed_id=str(sample_feed.id))

            assert result["success"] is True
            assert result["feed_id"] == str(sample_feed.id)
            assert result["feed_name"] == sample_feed.name
            assert result["entry_count"] == len(sample_blog_entries)
            assert "last_fetched" in result

    async def test_handles_feed_not_found(self, mock_feeds_ctx: dict, mock_session_maker: AsyncMock) -> None:
        """Test handling when feed doesn't exist."""
        feed_id = uuid4()

        with patch("pydotorg.domains.blogs.services.FeedService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get = AsyncMock(return_value=None)

            from pydotorg.tasks.feeds import refresh_single_feed

            result = await refresh_single_feed(mock_feeds_ctx, feed_id=str(feed_id))

            assert result["success"] is False
            assert "not found" in result["error"].lower()
            assert result["feed_id"] == str(feed_id)

    async def test_handles_inactive_feed(
        self, mock_feeds_ctx: dict, mock_session_maker: AsyncMock, sample_feed: Feed
    ) -> None:
        """Test handling when feed is inactive."""
        original_active = sample_feed.is_active
        sample_feed.is_active = False

        try:
            with patch("pydotorg.domains.blogs.services.FeedService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get = AsyncMock(return_value=sample_feed)

                from pydotorg.tasks.feeds import refresh_single_feed

                result = await refresh_single_feed(mock_feeds_ctx, feed_id=str(sample_feed.id))

                assert result["success"] is False
                assert "not active" in result["error"].lower()
                assert result["feed_name"] == sample_feed.name
        finally:
            sample_feed.is_active = original_active

    async def test_handles_invalid_uuid(self, mock_feeds_ctx: dict, mock_session_maker: AsyncMock) -> None:
        """Test handling invalid feed_id format."""
        from pydotorg.tasks.feeds import refresh_single_feed

        result = await refresh_single_feed(mock_feeds_ctx, feed_id="not-a-uuid")

        assert result["success"] is False
        assert "Invalid feed_id format" in result["error"]

    async def test_raises_on_fetch_failure(
        self, mock_feeds_ctx: dict, mock_session_maker: AsyncMock, sample_feed: Feed
    ) -> None:
        """Test that fetch failures raise exceptions."""
        with patch("pydotorg.domains.blogs.services.FeedService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get = AsyncMock(return_value=sample_feed)
            mock_service.fetch_feed = AsyncMock(side_effect=RuntimeError("Connection timeout"))

            from pydotorg.tasks.feeds import refresh_single_feed

            with pytest.raises(RuntimeError):
                await refresh_single_feed(mock_feeds_ctx, feed_id=str(sample_feed.id))


@pytest.mark.unit
class TestCronJobs:
    """Test suite for cron job configurations."""

    def test_cron_refresh_feeds_exists(self) -> None:
        """Test that cron job for refresh_stale_feeds exists."""
        from pydotorg.tasks.feeds import cron_refresh_feeds

        assert cron_refresh_feeds is not None
        assert cron_refresh_feeds.cron == "*/15 * * * *"
        assert cron_refresh_feeds.timeout == 600
        assert cron_refresh_feeds.kwargs == {"max_age_hours": 1}

    def test_cron_calls_correct_function(self) -> None:
        """Test that cron job calls refresh_stale_feeds."""
        from pydotorg.tasks.feeds import cron_refresh_feeds, refresh_stale_feeds

        assert cron_refresh_feeds.function == refresh_stale_feeds

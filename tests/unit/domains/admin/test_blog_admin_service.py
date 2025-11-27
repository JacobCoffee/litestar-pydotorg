"""Unit tests for BlogAdminService."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest

from pydotorg.domains.admin.services.blogs import BlogAdminService
from pydotorg.domains.blogs.models import BlogEntry, Feed


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock async session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_feed() -> Mock:
    """Create a mock feed."""
    feed = Mock(spec=Feed)
    feed.id = uuid4()
    feed.name = "Test Feed"
    feed.website_url = "https://example.com"
    feed.feed_url = "https://example.com/feed.xml"
    feed.last_fetched = datetime.now(tz=UTC)
    feed.is_active = True
    feed.entries = []
    feed.created_at = datetime.now(tz=UTC)
    return feed


@pytest.fixture
def mock_entry() -> Mock:
    """Create a mock blog entry."""
    entry = Mock(spec=BlogEntry)
    entry.id = uuid4()
    entry.feed_id = uuid4()
    entry.title = "Test Blog Entry"
    entry.summary = "A test blog entry summary"
    entry.content = "This is the full content of the test blog entry"
    entry.url = "https://example.com/blog/test-entry"
    entry.pub_date = datetime.now(tz=UTC)
    entry.guid = "test-guid-12345"
    entry.feed = Mock()
    entry.created_at = datetime.now(tz=UTC)
    return entry


@pytest.fixture
def service(mock_session: AsyncMock) -> BlogAdminService:
    """Create a BlogAdminService instance with mock session."""
    return BlogAdminService(session=mock_session)


class TestListFeeds:
    """Tests for BlogAdminService.list_feeds."""

    async def test_list_feeds_returns_feeds_and_count(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
        mock_feed: Mock,
    ) -> None:
        """Test that list_feeds returns feeds and total count."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_feeds_result = MagicMock()
        mock_feeds_result.scalars.return_value.all.return_value = [mock_feed]

        mock_session.execute.side_effect = [mock_count_result, mock_feeds_result]

        feeds, total = await service.list_feeds()

        assert total == 1
        assert len(feeds) == 1
        assert feeds[0] == mock_feed

    async def test_list_feeds_with_is_active_filter(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
        mock_feed: Mock,
    ) -> None:
        """Test list_feeds with is_active filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_feeds_result = MagicMock()
        mock_feeds_result.scalars.return_value.all.return_value = [mock_feed]

        mock_session.execute.side_effect = [mock_count_result, mock_feeds_result]

        _feeds, total = await service.list_feeds(is_active=True)

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_feeds_with_search(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
        mock_feed: Mock,
    ) -> None:
        """Test list_feeds with search filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_feeds_result = MagicMock()
        mock_feeds_result.scalars.return_value.all.return_value = [mock_feed]

        mock_session.execute.side_effect = [mock_count_result, mock_feeds_result]

        _feeds, total = await service.list_feeds(search="Test")

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_feeds_with_pagination(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
        mock_feed: Mock,
    ) -> None:
        """Test list_feeds with pagination."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100

        mock_feeds_result = MagicMock()
        mock_feeds_result.scalars.return_value.all.return_value = [mock_feed]

        mock_session.execute.side_effect = [mock_count_result, mock_feeds_result]

        feeds, total = await service.list_feeds(limit=10, offset=20)

        assert total == 100
        assert len(feeds) == 1

    async def test_list_feeds_empty_result(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test list_feeds with no results."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_feeds_result = MagicMock()
        mock_feeds_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_feeds_result]

        feeds, total = await service.list_feeds()

        assert total == 0
        assert len(feeds) == 0


class TestListEntries:
    """Tests for BlogAdminService.list_entries."""

    async def test_list_entries_returns_entries_and_count(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
        mock_entry: Mock,
    ) -> None:
        """Test that list_entries returns entries and total count."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_entries_result = MagicMock()
        mock_entries_result.scalars.return_value.all.return_value = [mock_entry]

        mock_session.execute.side_effect = [mock_count_result, mock_entries_result]

        entries, total = await service.list_entries()

        assert total == 1
        assert len(entries) == 1
        assert entries[0] == mock_entry

    async def test_list_entries_with_feed_id_filter(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
        mock_entry: Mock,
    ) -> None:
        """Test list_entries with feed_id filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_entries_result = MagicMock()
        mock_entries_result.scalars.return_value.all.return_value = [mock_entry]

        mock_session.execute.side_effect = [mock_count_result, mock_entries_result]

        feed_id = uuid4()
        _entries, total = await service.list_entries(feed_id=feed_id)

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_entries_with_search(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
        mock_entry: Mock,
    ) -> None:
        """Test list_entries with search filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_entries_result = MagicMock()
        mock_entries_result.scalars.return_value.all.return_value = [mock_entry]

        mock_session.execute.side_effect = [mock_count_result, mock_entries_result]

        _entries, total = await service.list_entries(search="Test")

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_entries_with_pagination(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
        mock_entry: Mock,
    ) -> None:
        """Test list_entries with pagination."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50

        mock_entries_result = MagicMock()
        mock_entries_result.scalars.return_value.all.return_value = [mock_entry]

        mock_session.execute.side_effect = [mock_count_result, mock_entries_result]

        entries, total = await service.list_entries(limit=10, offset=5)

        assert total == 50
        assert len(entries) == 1

    async def test_list_entries_empty_result(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test list_entries with no results."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_entries_result = MagicMock()
        mock_entries_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_entries_result]

        entries, total = await service.list_entries()

        assert total == 0
        assert len(entries) == 0


class TestGetFeed:
    """Tests for BlogAdminService.get_feed."""

    async def test_get_feed_found(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
        mock_feed: Mock,
    ) -> None:
        """Test get_feed returns feed when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_feed
        mock_session.execute.return_value = mock_result

        feed = await service.get_feed(mock_feed.id)

        assert feed == mock_feed

    async def test_get_feed_not_found(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_feed returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        feed = await service.get_feed(uuid4())

        assert feed is None


class TestGetEntry:
    """Tests for BlogAdminService.get_entry."""

    async def test_get_entry_found(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
        mock_entry: Mock,
    ) -> None:
        """Test get_entry returns entry when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_entry
        mock_session.execute.return_value = mock_result

        entry = await service.get_entry(mock_entry.id)

        assert entry == mock_entry

    async def test_get_entry_not_found(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_entry returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        entry = await service.get_entry(uuid4())

        assert entry is None


class TestActivateFeed:
    """Tests for BlogAdminService.activate_feed."""

    async def test_activate_feed_success(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
        mock_feed: Mock,
    ) -> None:
        """Test activating an existing feed."""
        mock_feed.is_active = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_feed
        mock_session.execute.return_value = mock_result

        feed = await service.activate_feed(mock_feed.id)

        assert feed.is_active is True
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_feed)

    async def test_activate_feed_not_found(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test activating non-existent feed returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        feed = await service.activate_feed(uuid4())

        assert feed is None
        mock_session.commit.assert_not_called()


class TestDeactivateFeed:
    """Tests for BlogAdminService.deactivate_feed."""

    async def test_deactivate_feed_success(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
        mock_feed: Mock,
    ) -> None:
        """Test deactivating an existing feed."""
        mock_feed.is_active = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_feed
        mock_session.execute.return_value = mock_result

        feed = await service.deactivate_feed(mock_feed.id)

        assert feed.is_active is False
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_feed)

    async def test_deactivate_feed_not_found(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test deactivating non-existent feed returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        feed = await service.deactivate_feed(uuid4())

        assert feed is None
        mock_session.commit.assert_not_called()


class TestGetStats:
    """Tests for BlogAdminService.get_stats."""

    async def test_get_stats_returns_all_counts(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_stats returns all blog statistics."""
        mock_total_feeds = MagicMock()
        mock_total_feeds.scalar.return_value = 50

        mock_active_feeds = MagicMock()
        mock_active_feeds.scalar.return_value = 35

        mock_inactive_feeds = MagicMock()
        mock_inactive_feeds.scalar.return_value = 15

        mock_total_entries = MagicMock()
        mock_total_entries.scalar.return_value = 500

        mock_entries_today = MagicMock()
        mock_entries_today.scalar.return_value = 10

        mock_session.execute.side_effect = [
            mock_total_feeds,
            mock_active_feeds,
            mock_inactive_feeds,
            mock_total_entries,
            mock_entries_today,
        ]

        stats = await service.get_stats()

        assert stats["total_feeds"] == 50
        assert stats["active_feeds"] == 35
        assert stats["inactive_feeds"] == 15
        assert stats["total_entries"] == 500
        assert stats["entries_today"] == 10
        assert mock_session.execute.call_count == 5

    async def test_get_stats_empty_database(
        self,
        service: BlogAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_stats with no feeds or entries."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0

        mock_session.execute.return_value = mock_result

        stats = await service.get_stats()

        assert stats["total_feeds"] == 0
        assert stats["active_feeds"] == 0
        assert stats["inactive_feeds"] == 0
        assert stats["total_entries"] == 0
        assert stats["entries_today"] == 0

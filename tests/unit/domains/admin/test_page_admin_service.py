"""Unit tests for PageAdminService."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest

from pydotorg.domains.admin.services.pages import PageAdminService
from pydotorg.domains.pages.models import ContentType, Page


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
def mock_page() -> Mock:
    """Create a mock page."""
    page = Mock(spec=Page)
    page.id = uuid4()
    page.title = "Test Page"
    page.path = "/test-page"
    page.content = "This is test content"
    page.description = "A test page description"
    page.content_type = ContentType.MARKDOWN
    page.is_published = True
    page.template_name = "pages/default.html"
    page.images = []
    page.documents = []
    page.created_at = datetime.now(tz=UTC)
    return page


@pytest.fixture
def service(mock_session: AsyncMock) -> PageAdminService:
    """Create a PageAdminService instance with mock session."""
    return PageAdminService(session=mock_session)


class TestListPages:
    """Tests for PageAdminService.list_pages."""

    async def test_list_pages_returns_pages_and_count(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
        mock_page: Mock,
    ) -> None:
        """Test that list_pages returns pages and total count."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_pages_result = MagicMock()
        mock_pages_result.scalars.return_value.all.return_value = [mock_page]

        mock_session.execute.side_effect = [mock_count_result, mock_pages_result]

        pages, total = await service.list_pages()

        assert total == 1
        assert len(pages) == 1
        assert pages[0] == mock_page

    async def test_list_pages_with_content_type_filter(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
        mock_page: Mock,
    ) -> None:
        """Test list_pages with content_type filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_pages_result = MagicMock()
        mock_pages_result.scalars.return_value.all.return_value = [mock_page]

        mock_session.execute.side_effect = [mock_count_result, mock_pages_result]

        _pages, total = await service.list_pages(content_type="markdown")

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_pages_with_is_published_filter(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
        mock_page: Mock,
    ) -> None:
        """Test list_pages with is_published filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_pages_result = MagicMock()
        mock_pages_result.scalars.return_value.all.return_value = [mock_page]

        mock_session.execute.side_effect = [mock_count_result, mock_pages_result]

        _pages, total = await service.list_pages(is_published=True)

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_pages_with_search(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
        mock_page: Mock,
    ) -> None:
        """Test list_pages with search filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_pages_result = MagicMock()
        mock_pages_result.scalars.return_value.all.return_value = [mock_page]

        mock_session.execute.side_effect = [mock_count_result, mock_pages_result]

        _pages, total = await service.list_pages(search="Test")

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_pages_with_pagination(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
        mock_page: Mock,
    ) -> None:
        """Test list_pages with pagination."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100

        mock_pages_result = MagicMock()
        mock_pages_result.scalars.return_value.all.return_value = [mock_page]

        mock_session.execute.side_effect = [mock_count_result, mock_pages_result]

        pages, total = await service.list_pages(limit=10, offset=20)

        assert total == 100
        assert len(pages) == 1

    async def test_list_pages_empty_result(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test list_pages with no results."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_pages_result = MagicMock()
        mock_pages_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_pages_result]

        pages, total = await service.list_pages()

        assert total == 0
        assert len(pages) == 0


class TestGetPage:
    """Tests for PageAdminService.get_page."""

    async def test_get_page_found(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
        mock_page: Mock,
    ) -> None:
        """Test get_page returns page when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_page
        mock_session.execute.return_value = mock_result

        page = await service.get_page(mock_page.id)

        assert page == mock_page

    async def test_get_page_not_found(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_page returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        page = await service.get_page(uuid4())

        assert page is None


class TestGetPageByPath:
    """Tests for PageAdminService.get_page_by_path."""

    async def test_get_page_by_path_found(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
        mock_page: Mock,
    ) -> None:
        """Test get_page_by_path returns page when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_page
        mock_session.execute.return_value = mock_result

        page = await service.get_page_by_path("/test-page")

        assert page == mock_page

    async def test_get_page_by_path_not_found(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_page_by_path returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        page = await service.get_page_by_path("/nonexistent")

        assert page is None


class TestPublishPage:
    """Tests for PageAdminService.publish_page."""

    async def test_publish_page_success(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
        mock_page: Mock,
    ) -> None:
        """Test publishing an existing page."""
        mock_page.is_published = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_page
        mock_session.execute.return_value = mock_result

        page = await service.publish_page(mock_page.id)

        assert page.is_published is True
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_page)

    async def test_publish_page_not_found(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test publishing non-existent page returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        page = await service.publish_page(uuid4())

        assert page is None
        mock_session.commit.assert_not_called()


class TestUnpublishPage:
    """Tests for PageAdminService.unpublish_page."""

    async def test_unpublish_page_success(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
        mock_page: Mock,
    ) -> None:
        """Test unpublishing an existing page."""
        mock_page.is_published = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_page
        mock_session.execute.return_value = mock_result

        page = await service.unpublish_page(mock_page.id)

        assert page.is_published is False
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_page)

    async def test_unpublish_page_not_found(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test unpublishing non-existent page returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        page = await service.unpublish_page(uuid4())

        assert page is None
        mock_session.commit.assert_not_called()


class TestGetStats:
    """Tests for PageAdminService.get_stats."""

    async def test_get_stats_returns_all_counts(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_stats returns all page statistics."""
        mock_total_pages = MagicMock()
        mock_total_pages.scalar.return_value = 100

        mock_published = MagicMock()
        mock_published.scalar.return_value = 75

        mock_unpublished = MagicMock()
        mock_unpublished.scalar.return_value = 25

        mock_markdown = MagicMock()
        mock_markdown.scalar.return_value = 60

        mock_html = MagicMock()
        mock_html.scalar.return_value = 30

        mock_rst = MagicMock()
        mock_rst.scalar.return_value = 10

        mock_session.execute.side_effect = [
            mock_total_pages,
            mock_published,
            mock_unpublished,
            mock_markdown,
            mock_html,
            mock_rst,
        ]

        stats = await service.get_stats()

        assert stats["total_pages"] == 100
        assert stats["published_pages"] == 75
        assert stats["unpublished_pages"] == 25
        assert stats["markdown_pages"] == 60
        assert stats["html_pages"] == 30
        assert stats["rst_pages"] == 10
        assert mock_session.execute.call_count == 6

    async def test_get_stats_empty_database(
        self,
        service: PageAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_stats with no pages."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0

        mock_session.execute.return_value = mock_result

        stats = await service.get_stats()

        assert stats["total_pages"] == 0
        assert stats["published_pages"] == 0
        assert stats["unpublished_pages"] == 0
        assert stats["markdown_pages"] == 0
        assert stats["html_pages"] == 0
        assert stats["rst_pages"] == 0

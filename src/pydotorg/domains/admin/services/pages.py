"""Admin page management service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from pydotorg.domains.pages.models import ContentType, Page
from pydotorg.lib.tasks import enqueue_task

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class PageAdminService:
    """Service for admin page management operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_pages(
        self,
        limit: int = 20,
        offset: int = 0,
        content_type: str | None = None,
        search: str | None = None,
        *,
        is_published: bool | None = None,
    ) -> tuple[list[Page], int]:
        """List pages with filtering and pagination.

        Args:
            limit: Maximum number of pages to return
            offset: Number of pages to skip
            content_type: Filter by content type
            is_published: Filter by published status
            search: Search query for page title or content

        Returns:
            Tuple of (pages list, total count)
        """
        query = select(Page).options(
            selectinload(Page.images),
            selectinload(Page.documents),
        )

        if content_type:
            content_type_enum = ContentType(content_type)
            query = query.where(Page.content_type == content_type_enum)

        if is_published is not None:
            query = query.where(Page.is_published == is_published)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Page.title.ilike(search_term),
                    Page.content.ilike(search_term),
                    Page.description.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Page.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        pages = list(result.scalars().all())

        return pages, total

    async def get_page(self, page_id: UUID) -> Page | None:
        """Get a page by ID.

        Args:
            page_id: Page ID

        Returns:
            Page if found, None otherwise
        """
        query = (
            select(Page)
            .where(Page.id == page_id)
            .options(
                selectinload(Page.images),
                selectinload(Page.documents),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_page_by_path(self, path: str) -> Page | None:
        """Get a page by path.

        Args:
            path: Page path

        Returns:
            Page if found, None otherwise
        """
        query = (
            select(Page)
            .where(Page.path == path)
            .options(
                selectinload(Page.images),
                selectinload(Page.documents),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def publish_page(self, page_id: UUID) -> Page | None:
        """Publish a page.

        Args:
            page_id: Page ID

        Returns:
            Updated page if found, None otherwise
        """
        page = await self.get_page(page_id)
        if not page:
            return None

        page.is_published = True
        await self.session.commit()
        await self.session.refresh(page)

        await enqueue_task("index_page", page_id=str(page.id))
        await enqueue_task("invalidate_page_response_cache", page_path=page.path)

        return page

    async def unpublish_page(self, page_id: UUID) -> Page | None:
        """Unpublish a page.

        Args:
            page_id: Page ID

        Returns:
            Updated page if found, None otherwise
        """
        page = await self.get_page(page_id)
        if not page:
            return None

        page.is_published = False
        await self.session.commit()
        await self.session.refresh(page)

        await enqueue_task("index_page", page_id=str(page.id))
        await enqueue_task("invalidate_page_response_cache", page_path=page.path)

        return page

    async def get_stats(self) -> dict:
        """Get page statistics.

        Returns:
            Dictionary with page stats
        """
        total_pages_query = select(func.count()).select_from(Page)
        total_pages_result = await self.session.execute(total_pages_query)
        total_pages = total_pages_result.scalar() or 0

        published_query = select(func.count()).where(Page.is_published)
        published_result = await self.session.execute(published_query)
        published_pages = published_result.scalar() or 0

        unpublished_query = select(func.count()).where(~Page.is_published)
        unpublished_result = await self.session.execute(unpublished_query)
        unpublished_pages = unpublished_result.scalar() or 0

        markdown_query = select(func.count()).where(Page.content_type == ContentType.MARKDOWN)
        markdown_result = await self.session.execute(markdown_query)
        markdown_pages = markdown_result.scalar() or 0

        html_query = select(func.count()).where(Page.content_type == ContentType.HTML)
        html_result = await self.session.execute(html_query)
        html_pages = html_result.scalar() or 0

        rst_query = select(func.count()).where(Page.content_type == ContentType.RESTRUCTUREDTEXT)
        rst_result = await self.session.execute(rst_query)
        rst_pages = rst_result.scalar() or 0

        return {
            "total_pages": total_pages,
            "published_pages": published_pages,
            "unpublished_pages": unpublished_pages,
            "markdown_pages": markdown_pages,
            "html_pages": html_pages,
            "rst_pages": rst_pages,
        }

    async def delete_page(self, page_id: UUID) -> bool:
        """Delete a page.

        Args:
            page_id: Page ID

        Returns:
            True if deleted, False if not found
        """
        page = await self.get_page(page_id)
        if not page:
            return False

        page_path = page.path
        await self.session.delete(page)
        await self.session.commit()

        await enqueue_task("remove_page_from_index", page_id=str(page_id))
        await enqueue_task("invalidate_page_response_cache", page_path=page_path)

        return True

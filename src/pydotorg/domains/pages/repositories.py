"""Pages domain repositories for database access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from pydotorg.domains.pages.models import DocumentFile, Image, Page

if TYPE_CHECKING:
    from uuid import UUID


class PageRepository(SQLAlchemyAsyncRepository[Page]):
    """Repository for Page database operations."""

    model_type = Page

    async def get_by_path(self, path: str) -> Page | None:
        """Get a page by its URL path.

        Args:
            path: The URL path to search for.

        Returns:
            The page if found, None otherwise.
        """
        statement = select(Page).where(Page.path == path)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_published(self, limit: int = 100, offset: int = 0) -> list[Page]:
        """List published pages.

        Args:
            limit: Maximum number of pages to return.
            offset: Number of pages to skip.

        Returns:
            List of published pages.
        """
        statement = select(Page).where(Page.is_published.is_(True)).limit(limit).offset(offset)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def exists_by_path(self, path: str) -> bool:
        """Check if a page exists by path.

        Args:
            path: The path to check.

        Returns:
            True if a page with this path exists, False otherwise.
        """
        page = await self.get_by_path(path)
        return page is not None


class ImageRepository(SQLAlchemyAsyncRepository[Image]):
    """Repository for Image database operations."""

    model_type = Image

    async def list_by_page_id(self, page_id: UUID, limit: int = 100, offset: int = 0) -> list[Image]:
        """List images for a specific page.

        Args:
            page_id: The page ID to filter by.
            limit: Maximum number of images to return.
            offset: Number of images to skip.

        Returns:
            List of images for the page.
        """
        statement = select(Image).where(Image.page_id == page_id).limit(limit).offset(offset)
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class DocumentFileRepository(SQLAlchemyAsyncRepository[DocumentFile]):
    """Repository for DocumentFile database operations."""

    model_type = DocumentFile

    async def list_by_page_id(self, page_id: UUID, limit: int = 100, offset: int = 0) -> list[DocumentFile]:
        """List document files for a specific page.

        Args:
            page_id: The page ID to filter by.
            limit: Maximum number of documents to return.
            offset: Number of documents to skip.

        Returns:
            List of document files for the page.
        """
        statement = select(DocumentFile).where(DocumentFile.page_id == page_id).limit(limit).offset(offset)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

"""Pages domain services for business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from pydotorg.domains.pages.models import ContentType, DocumentFile, Image, Page
from pydotorg.domains.pages.repositories import DocumentFileRepository, ImageRepository, PageRepository
from pydotorg.lib.tasks import enqueue_task

if TYPE_CHECKING:
    from uuid import UUID

    from pydotorg.domains.pages.schemas import DocumentFileCreate, ImageCreate, PageCreate

try:
    import cmarkgfm

    CMARKGFM_AVAILABLE = True
except ImportError:
    CMARKGFM_AVAILABLE = False

try:
    import markdown

    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    import docutils.core

    DOCUTILS_AVAILABLE = True
except ImportError:
    DOCUTILS_AVAILABLE = False


class PageService(SQLAlchemyAsyncRepositoryService[Page]):
    """Service for Page business logic."""

    repository_type = PageRepository
    match_fields = ["path"]

    async def create(self, data: dict) -> Page:  # type: ignore[override]
        """Create a new page.

        Args:
            data: Page creation data.

        Returns:
            The created page instance.
        """
        page = await super().create(data)
        await self.session.commit()

        await enqueue_task("index_page", page_id=str(page.id))

        return page

    async def update(self, item_id: UUID, data: dict) -> Page:  # type: ignore[override]
        """Update a page.

        Args:
            item_id: The page ID.
            data: Update data.

        Returns:
            The updated page instance.
        """
        page = await super().update(item_id, data)
        await self.session.commit()

        await enqueue_task("index_page", page_id=str(page.id))
        await enqueue_task("invalidate_page_response_cache", page_path=page.path)

        return page

    async def create_page(self, data: PageCreate) -> Page:
        """Create a new page.

        Args:
            data: Page creation data.

        Returns:
            The created page instance.

        Raises:
            ValueError: If path already exists.
        """
        if await self.repository.exists_by_path(data.path):
            msg = f"Page with path {data.path} already exists"
            raise ValueError(msg)

        return await self.create(data.model_dump())

    async def get_by_path(self, path: str) -> Page | None:
        """Get a page by its URL path.

        Args:
            path: The URL path to search for.

        Returns:
            The page if found, None otherwise.
        """
        return await self.repository.get_by_path(path)

    async def list_published(self, limit: int = 100, offset: int = 0) -> list[Page]:
        """List published pages.

        Args:
            limit: Maximum number of pages to return.
            offset: Number of pages to skip.

        Returns:
            List of published pages.
        """
        return await self.repository.list_published(limit=limit, offset=offset)

    async def publish(self, page_id: UUID) -> Page:
        """Publish a page.

        Args:
            page_id: The ID of the page to publish.

        Returns:
            The updated page instance.
        """
        return await self.update(page_id, {"is_published": True})

    async def unpublish(self, page_id: UUID) -> Page:
        """Unpublish a page.

        Args:
            page_id: The ID of the page to unpublish.

        Returns:
            The updated page instance.
        """
        return await self.update(page_id, {"is_published": False})

    async def render_content(self, page: Page) -> str:
        """Render page content based on content type.

        Args:
            page: The page to render.

        Returns:
            Rendered HTML content.
        """
        if page.content_type == ContentType.MARKDOWN:
            return self._render_markdown(page.content)
        if page.content_type == ContentType.RESTRUCTUREDTEXT:
            return self._render_rst(page.content)
        return page.content

    def _render_markdown(self, content: str) -> str:
        """Render markdown content to HTML.

        Args:
            content: The markdown content.

        Returns:
            HTML string.

        Raises:
            ImportError: If neither cmarkgfm nor markdown is available.
        """
        if CMARKGFM_AVAILABLE:
            return cmarkgfm.github_flavored_markdown_to_html(content)
        if MARKDOWN_AVAILABLE:
            return markdown.markdown(content, extensions=["extra", "codehilite"])
        msg = "Neither cmarkgfm nor markdown library is installed"
        raise ImportError(msg)

    def _render_rst(self, content: str) -> str:
        """Render reStructuredText content to HTML.

        Args:
            content: The RST content.

        Returns:
            HTML string.

        Raises:
            ImportError: If docutils is not available.
        """
        if not DOCUTILS_AVAILABLE:
            msg = "docutils library is not installed"
            raise ImportError(msg)

        parts = docutils.core.publish_parts(content, writer_name="html")
        return parts["html_body"]


class ImageService(SQLAlchemyAsyncRepositoryService[Image]):
    """Service for Image business logic."""

    repository_type = ImageRepository
    match_fields = ["page_id"]

    async def list_by_page_id(self, page_id: UUID, limit: int = 100, offset: int = 0) -> list[Image]:
        """List images for a specific page.

        Args:
            page_id: The page ID to filter by.
            limit: Maximum number of images to return.
            offset: Number of images to skip.

        Returns:
            List of images for the page.
        """
        return await self.repository.list_by_page_id(page_id, limit=limit, offset=offset)

    async def create_image(self, data: ImageCreate) -> Image:
        """Create a new image for a page.

        Args:
            data: Image creation data.

        Returns:
            The created image instance.
        """
        return await self.create(data.model_dump())


class DocumentFileService(SQLAlchemyAsyncRepositoryService[DocumentFile]):
    """Service for DocumentFile business logic."""

    repository_type = DocumentFileRepository
    match_fields = ["page_id"]

    async def list_by_page_id(self, page_id: UUID, limit: int = 100, offset: int = 0) -> list[DocumentFile]:
        """List document files for a specific page.

        Args:
            page_id: The page ID to filter by.
            limit: Maximum number of documents to return.
            offset: Number of documents to skip.

        Returns:
            List of document files for the page.
        """
        return await self.repository.list_by_page_id(page_id, limit=limit, offset=offset)

    async def create_document(self, data: DocumentFileCreate) -> DocumentFile:
        """Create a new document file for a page.

        Args:
            data: Document file creation data.

        Returns:
            The created document file instance.
        """
        return await self.create(data.model_dump())

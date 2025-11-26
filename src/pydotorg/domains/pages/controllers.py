"""Pages domain API controllers."""

from __future__ import annotations

from typing import Annotated

from litestar import Controller, delete, get, patch, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Parameter
from litestar.response import Template

from pydotorg.domains.pages.schemas import (
    DocumentFileCreate,
    DocumentFileRead,
    ImageCreate,
    ImageRead,
    PageCreate,
    PagePublic,
    PageRead,
    PageUpdate,
)

from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from pydotorg.domains.pages.services import DocumentFileService, ImageService, PageService


class PageController(Controller):
    """Controller for Page CRUD operations."""

    path = "/api/v1/pages"
    tags = ["pages"]

    @get("/")
    async def list_pages(
        self,
        page_service: PageService,
        limit_offset: LimitOffset,
    ) -> list[PageRead]:
        """List all pages with pagination."""
        pages, _total = await page_service.list_and_count(limit_offset)
        return [PageRead.model_validate(page) for page in pages]

    @get("/published")
    async def list_published_pages(
        self,
        page_service: PageService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[PagePublic]:
        """List published pages."""
        pages = await page_service.list_published(limit=limit, offset=offset)
        return [PagePublic.model_validate(page) for page in pages]

    @get("/{page_id:uuid}")
    async def get_page(
        self,
        page_service: PageService,
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
    ) -> PageRead:
        """Get a page by ID."""
        page = await page_service.get(page_id)
        return PageRead.model_validate(page)

    @post("/path")
    async def get_page_by_path(
        self,
        page_service: PageService,
        data: dict[str, str],
    ) -> PagePublic:
        """Get a page by path."""
        path = data.get("path")
        if not path:
            msg = "Path is required"
            raise ValueError(msg)

        page = await page_service.get_by_path(path)
        if not page:
            msg = f"Page with path {path} not found"
            raise NotFoundException(msg)
        return PagePublic.model_validate(page)

    @post("/")
    async def create_page(
        self,
        page_service: PageService,
        data: PageCreate,
    ) -> PageRead:
        """Create a new page."""
        page = await page_service.create_page(data)
        return PageRead.model_validate(page)

    @put("/{page_id:uuid}")
    async def update_page(
        self,
        page_service: PageService,
        data: PageUpdate,
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
    ) -> PageRead:
        """Update a page."""
        update_data = data.model_dump(exclude_unset=True)
        page = await page_service.update(page_id, update_data)
        return PageRead.model_validate(page)

    @patch("/{page_id:uuid}/publish")
    async def publish_page(
        self,
        page_service: PageService,
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
    ) -> PageRead:
        """Publish a page."""
        page = await page_service.publish(page_id)
        return PageRead.model_validate(page)

    @patch("/{page_id:uuid}/unpublish")
    async def unpublish_page(
        self,
        page_service: PageService,
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
    ) -> PageRead:
        """Unpublish a page."""
        page = await page_service.unpublish(page_id)
        return PageRead.model_validate(page)

    @delete("/{page_id:uuid}")
    async def delete_page(
        self,
        page_service: PageService,
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
    ) -> None:
        """Delete a page."""
        await page_service.delete(page_id)


class PageRenderController(Controller):
    """Controller for rendering pages as HTML."""

    path = ""
    tags = ["pages-render"]

    @get("/{path:path}")
    async def render_page(
        self,
        page_service: PageService,
        path: Annotated[str, Parameter(title="Page Path", description="The page URL path")],
    ) -> Template:
        """Render a page as HTML."""
        page_path = f"/{path}/"
        page = await page_service.get_by_path(page_path)

        if not page or not page.is_published:
            msg = "Page not found"
            raise NotFoundException(msg)

        rendered_content = await page_service.render_content(page)

        return Template(
            template_name=page.template_name,
            context={
                "page": page,
                "content": rendered_content,
                "title": page.title,
                "description": page.description,
                "keywords": page.keywords,
            },
        )


class ImageController(Controller):
    """Controller for Image CRUD operations."""

    path = "/api/v1"
    tags = ["images"]

    @get("/pages/{page_id:uuid}/images")
    async def list_page_images(
        self,
        image_service: ImageService,
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[ImageRead]:
        """List images for a specific page."""
        images = await image_service.list_by_page_id(page_id, limit=limit, offset=offset)
        return [ImageRead.model_validate(image) for image in images]

    @get("/images/{image_id:uuid}")
    async def get_image(
        self,
        image_service: ImageService,
        image_id: Annotated[UUID, Parameter(title="Image ID", description="The image ID")],
    ) -> ImageRead:
        """Get an image by ID."""
        image = await image_service.get(image_id)
        return ImageRead.model_validate(image)

    @post("/pages/{page_id:uuid}/images")
    async def create_image(
        self,
        image_service: ImageService,
        data: ImageCreate,
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
    ) -> ImageRead:
        """Create a new image for a page."""
        data.page_id = page_id
        image = await image_service.create_image(data)
        return ImageRead.model_validate(image)

    @delete("/images/{image_id:uuid}")
    async def delete_image(
        self,
        image_service: ImageService,
        image_id: Annotated[UUID, Parameter(title="Image ID", description="The image ID")],
    ) -> None:
        """Delete an image."""
        await image_service.delete(image_id)


class DocumentFileController(Controller):
    """Controller for DocumentFile CRUD operations."""

    path = "/api/v1"
    tags = ["documents"]

    @get("/pages/{page_id:uuid}/documents")
    async def list_page_documents(
        self,
        document_file_service: DocumentFileService,
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[DocumentFileRead]:
        """List document files for a specific page."""
        documents = await document_file_service.list_by_page_id(page_id, limit=limit, offset=offset)
        return [DocumentFileRead.model_validate(doc) for doc in documents]

    @get("/documents/{document_id:uuid}")
    async def get_document(
        self,
        document_file_service: DocumentFileService,
        document_id: Annotated[UUID, Parameter(title="Document ID", description="The document ID")],
    ) -> DocumentFileRead:
        """Get a document file by ID."""
        document = await document_file_service.get(document_id)
        return DocumentFileRead.model_validate(document)

    @post("/pages/{page_id:uuid}/documents")
    async def create_document(
        self,
        document_file_service: DocumentFileService,
        data: DocumentFileCreate,
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
    ) -> DocumentFileRead:
        """Create a new document file for a page."""
        data.page_id = page_id
        document = await document_file_service.create_document(data)
        return DocumentFileRead.model_validate(document)

    @delete("/documents/{document_id:uuid}")
    async def delete_document(
        self,
        document_file_service: DocumentFileService,
        document_id: Annotated[UUID, Parameter(title="Document ID", description="The document ID")],
    ) -> None:
        """Delete a document file."""
        await document_file_service.delete(document_id)

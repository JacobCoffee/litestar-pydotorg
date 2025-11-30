"""Pages domain API controllers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, delete, get, patch, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Body, Parameter
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
from pydotorg.domains.pages.services import DocumentFileService, ImageService, PageService


class PageController(Controller):
    """Controller for Page CRUD operations."""

    path = "/api/v1/pages"
    tags = ["Pages"]

    @get("/")
    async def list_pages(
        self,
        page_service: PageService,
        limit_offset: LimitOffset,
    ) -> list[PagePublic]:
        """List all pages."""
        results, _total = await page_service.list_and_count(limit_offset)
        return [PagePublic.model_validate(page) for page in results]

    @get("/{page_id:uuid}")
    async def get_page(
        self,
        page_service: PageService,
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
    ) -> PageRead:
        """Get a page by ID."""
        page = await page_service.get(page_id)
        return PageRead.model_validate(page)

    @get("/by-path/{page_path:path}")
    async def get_page_by_path(
        self,
        page_service: PageService,
        page_path: Annotated[str, Parameter(title="Page Path", description="The page path")],
    ) -> PagePublic:
        """Get a page by path."""
        page = await page_service.get_one_or_none(path=f"/{page_path}")
        if page is None:
            raise NotFoundException(f"Page not found: /{page_path}")
        return PagePublic.model_validate(page)

    @post("/")
    async def create_page(
        self,
        page_service: PageService,
        data: Annotated[PageCreate, Body(title="Page", description="Page to create")],
    ) -> PageRead:
        """Create a new page."""
        page = await page_service.create(data.model_dump(exclude_unset=True))
        return PageRead.model_validate(page)

    @put("/{page_id:uuid}")
    async def update_page(
        self,
        page_service: PageService,
        data: Annotated[PageUpdate, Body(title="Page", description="Page data to update")],
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
    ) -> PageRead:
        """Update a page."""
        page = await page_service.update(data.model_dump(exclude_unset=True), item_id=page_id)
        return PageRead.model_validate(page)

    @patch("/{page_id:uuid}/publish")
    async def publish_page(
        self,
        page_service: PageService,
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
    ) -> PageRead:
        """Publish a page."""
        page = await page_service.update({"is_published": True}, item_id=page_id)
        return PageRead.model_validate(page)

    @patch("/{page_id:uuid}/unpublish")
    async def unpublish_page(
        self,
        page_service: PageService,
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
    ) -> PageRead:
        """Unpublish a page."""
        page = await page_service.update({"is_published": False}, item_id=page_id)
        return PageRead.model_validate(page)

    @delete("/{page_id:uuid}")
    async def delete_page(
        self,
        page_service: PageService,
        page_id: Annotated[UUID, Parameter(title="Page ID", description="The page ID")],
    ) -> None:
        """Delete a page."""
        await page_service.delete(page_id)


class ImageController(Controller):
    """Controller for Image CRUD operations."""

    path = "/api/v1/images"
    tags = ["Pages"]

    @get("/")
    async def list_images(
        self,
        image_service: ImageService,
        limit_offset: LimitOffset,
    ) -> list[ImageRead]:
        """List all images."""
        results, _total = await image_service.list_and_count(limit_offset)
        return [ImageRead.model_validate(image) for image in results]

    @get("/{image_id:uuid}")
    async def get_image(
        self,
        image_service: ImageService,
        image_id: Annotated[UUID, Parameter(title="Image ID", description="The image ID")],
    ) -> ImageRead:
        """Get an image by ID."""
        image = await image_service.get(image_id)
        return ImageRead.model_validate(image)

    @post("/")
    async def create_image(
        self,
        image_service: ImageService,
        data: Annotated[ImageCreate, Body(title="Image", description="Image to create")],
    ) -> ImageRead:
        """Create a new image."""
        image = await image_service.create(data.model_dump(exclude_unset=True))
        return ImageRead.model_validate(image)

    @delete("/{image_id:uuid}")
    async def delete_image(
        self,
        image_service: ImageService,
        image_id: Annotated[UUID, Parameter(title="Image ID", description="The image ID")],
    ) -> None:
        """Delete an image."""
        await image_service.delete(image_id)


class DocumentFileController(Controller):
    """Controller for Document File CRUD operations."""

    path = "/api/v1/documents"
    tags = ["Pages"]

    @get("/")
    async def list_documents(
        self,
        document_service: DocumentFileService,
        limit_offset: LimitOffset,
    ) -> list[DocumentFileRead]:
        """List all documents."""
        results, _total = await document_service.list_and_count(limit_offset)
        return [DocumentFileRead.model_validate(doc) for doc in results]

    @get("/{document_id:uuid}")
    async def get_document(
        self,
        document_service: DocumentFileService,
        document_id: Annotated[UUID, Parameter(title="Document ID", description="The document ID")],
    ) -> DocumentFileRead:
        """Get a document by ID."""
        document = await document_service.get(document_id)
        return DocumentFileRead.model_validate(document)

    @post("/")
    async def create_document(
        self,
        document_service: DocumentFileService,
        data: Annotated[DocumentFileCreate, Body(title="Document File", description="Document to create")],
    ) -> DocumentFileRead:
        """Create a new document."""
        document = await document_service.create(data.model_dump(exclude_unset=True))
        return DocumentFileRead.model_validate(document)

    @delete("/{document_id:uuid}")
    async def delete_document(
        self,
        document_service: DocumentFileService,
        document_id: Annotated[UUID, Parameter(title="Document ID", description="The document ID")],
    ) -> None:
        """Delete a document."""
        await document_service.delete(document_id)


class PageRenderController(Controller):
    """Controller for rendering page templates."""

    path = "/{page_path:path}"
    include_in_schema = False

    @get("/")
    async def render_page(
        self,
        page_service: PageService,
        page_path: str,
    ) -> Template:
        """Render a page template by path."""
        path = f"/{page_path.lstrip('/')}" if page_path else "/"
        page = await page_service.get_one_or_none(path=path, is_published=True)
        if page is None:
            raise NotFoundException(f"Page not found: {path}")

        return Template(
            template_name=page.template_name or "pages/default.html.jinja2",
            context={"page": page},
        )

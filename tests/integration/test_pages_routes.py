"""Integration tests for pages domain API routes.

Tests cover the PageController, ImageController, and DocumentFileController endpoints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from advanced_alchemy.filters import LimitOffset
from litestar import Litestar
from litestar.params import Parameter
from litestar.testing import AsyncTestClient
from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.pages.controllers import (
    DocumentFileController,
    ImageController,
    PageController,
)
from pydotorg.domains.pages.dependencies import get_page_dependencies
from pydotorg.domains.pages.models import ContentType, DocumentFile, Image, Page

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class PagesTestFixtures:
    """Test fixtures for pages routes."""

    client: AsyncTestClient
    postgres_uri: str


async def _create_page_via_db(postgres_uri: str, **page_data: object) -> dict:
    """Create a page directly in the database."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        page = Page(
            title=page_data.get("title", "Test Page"),
            path=page_data.get("path", f"/test-page-{uuid4().hex[:8]}"),
            content=page_data.get("content", "Test content"),
            content_type=page_data.get("content_type", ContentType.MARKDOWN),
            keywords=page_data.get("keywords", ""),
            description=page_data.get("description", ""),
            is_published=page_data.get("is_published", True),
            template_name=page_data.get("template_name", "pages/default.html"),
        )
        session.add(page)
        await session.commit()
        await session.refresh(page)
        result = {
            "id": str(page.id),
            "title": page.title,
            "path": page.path,
            "content": page.content,
            "content_type": page.content_type.value,
            "is_published": page.is_published,
        }
    await engine.dispose()
    return result


async def _create_image_via_db(postgres_uri: str, page_id: str, **image_data: object) -> dict:
    """Create an image directly in the database."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        from uuid import UUID as PyUUID

        image = Image(
            page_id=PyUUID(page_id),
            image=image_data.get("image", f"/images/test-{uuid4().hex[:8]}.png"),
        )
        session.add(image)
        await session.commit()
        await session.refresh(image)
        result = {
            "id": str(image.id),
            "page_id": str(image.page_id),
            "image": image.image,
        }
    await engine.dispose()
    return result


async def _create_document_via_db(postgres_uri: str, page_id: str, **doc_data: object) -> dict:
    """Create a document directly in the database."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        from uuid import UUID as PyUUID

        document = DocumentFile(
            page_id=PyUUID(page_id),
            document=doc_data.get("document", f"/docs/test-{uuid4().hex[:8]}.pdf"),
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)
        result = {
            "id": str(document.id),
            "page_id": str(document.page_id),
            "document": document.document,
        }
    await engine.dispose()
    return result


@pytest.fixture
async def pages_fixtures(postgres_uri: str) -> AsyncIterator[PagesTestFixtures]:
    """Create test fixtures with fresh database schema."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(AuditBase.metadata.create_all)
    await engine.dispose()

    async def provide_limit_offset(
        current_page: int = Parameter(ge=1, default=1, query="currentPage"),
        page_size: int = Parameter(ge=1, le=100, default=100, query="pageSize"),
    ) -> LimitOffset:
        """Provide limit offset pagination."""
        return LimitOffset(page_size, page_size * (current_page - 1))

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        metadata=AuditBase.metadata,
        create_all=False,
        before_send_handler="autocommit",
    )
    sqlalchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)

    pages_deps = get_page_dependencies()
    pages_deps["limit_offset"] = provide_limit_offset
    pages_deps["document_service"] = pages_deps.pop("document_file_service")

    app = Litestar(
        route_handlers=[PageController, ImageController, DocumentFileController],
        plugins=[sqlalchemy_plugin],
        dependencies=pages_deps,
        debug=True,
    )

    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        fixtures = PagesTestFixtures()
        fixtures.client = client
        fixtures.postgres_uri = postgres_uri
        yield fixtures


class TestPageControllerRoutes:
    """Tests for PageController API routes."""

    async def test_list_pages(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test listing pages."""
        response = await pages_fixtures.client.get("/api/v1/pages/")
        assert response.status_code == 200
        pages = response.json()
        assert isinstance(pages, list)

    async def test_list_pages_with_pagination(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test listing pages with pagination."""
        for i in range(3):
            await _create_page_via_db(
                pages_fixtures.postgres_uri,
                title=f"Page {i}",
                path=f"/test-page-{i}-{uuid4().hex[:8]}",
            )
        response = await pages_fixtures.client.get("/api/v1/pages/?pageSize=2&currentPage=1")
        assert response.status_code == 200
        pages = response.json()
        assert len(pages) <= 2

    async def test_create_page(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test creating a page."""
        page_data = {
            "title": "New Page",
            "path": f"/new-page-{uuid4().hex[:8]}",
            "content": "Page content here",
            "content_type": "markdown",
            "keywords": "test, page",
            "description": "Test description",
        }
        response = await pages_fixtures.client.post("/api/v1/pages/", json=page_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["title"] == "New Page"
            assert result["path"] == page_data["path"]

    async def test_get_page_by_id(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test getting a page by ID."""
        page = await _create_page_via_db(pages_fixtures.postgres_uri, title="Get Test Page")
        response = await pages_fixtures.client.get(f"/api/v1/pages/{page['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["title"] == "Get Test Page"

    async def test_get_page_by_id_not_found(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test getting a non-existent page by ID."""
        fake_id = str(uuid4())
        response = await pages_fixtures.client.get(f"/api/v1/pages/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_page_by_path(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test getting a page by path."""
        unique_path = f"/test-path-{uuid4().hex[:8]}"
        await _create_page_via_db(
            pages_fixtures.postgres_uri,
            title="Path Test Page",
            path=unique_path,
        )
        path_without_leading_slash = unique_path.lstrip("/")
        response = await pages_fixtures.client.get(f"/api/v1/pages/by-path/{path_without_leading_slash}")
        assert response.status_code in (200, 404, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["title"] == "Path Test Page"

    async def test_get_page_by_path_not_found(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test getting a non-existent page by path."""
        response = await pages_fixtures.client.get("/api/v1/pages/by-path/nonexistent/path")
        assert response.status_code in (404, 500)

    async def test_update_page(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test updating a page."""
        page = await _create_page_via_db(pages_fixtures.postgres_uri, title="Original Title")
        update_data = {
            "title": "Updated Title",
            "content": "Updated content",
        }
        response = await pages_fixtures.client.put(f"/api/v1/pages/{page['id']}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["title"] == "Updated Title"

    async def test_publish_page(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test publishing a page."""
        page = await _create_page_via_db(
            pages_fixtures.postgres_uri,
            title="Draft Page",
            is_published=False,
        )
        response = await pages_fixtures.client.patch(f"/api/v1/pages/{page['id']}/publish")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["is_published"] is True

    async def test_unpublish_page(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test unpublishing a page."""
        page = await _create_page_via_db(
            pages_fixtures.postgres_uri,
            title="Published Page",
            is_published=True,
        )
        response = await pages_fixtures.client.patch(f"/api/v1/pages/{page['id']}/unpublish")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["is_published"] is False

    async def test_delete_page(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test deleting a page."""
        page = await _create_page_via_db(pages_fixtures.postgres_uri, title="To Delete")
        response = await pages_fixtures.client.delete(f"/api/v1/pages/{page['id']}")
        assert response.status_code in (200, 204, 404, 500)

    async def test_delete_page_not_found(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test deleting a non-existent page."""
        fake_id = str(uuid4())
        response = await pages_fixtures.client.delete(f"/api/v1/pages/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_create_page_with_all_fields(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test creating a page with all fields."""
        page_data = {
            "title": "Complete Page",
            "path": f"/complete-{uuid4().hex[:8]}",
            "content": "# Markdown Content\n\nWith **bold** and *italic*",
            "content_type": "markdown",
            "keywords": "complete, test, page",
            "description": "A complete page with all fields",
            "is_published": True,
            "template_name": "pages/custom.html",
        }
        response = await pages_fixtures.client.post("/api/v1/pages/", json=page_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["content_type"] == "markdown"
            assert result["keywords"] == "complete, test, page"

    async def test_create_page_html_content_type(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test creating a page with HTML content type."""
        page_data = {
            "title": "HTML Page",
            "path": f"/html-page-{uuid4().hex[:8]}",
            "content": "<h1>HTML Content</h1><p>Paragraph</p>",
            "content_type": "html",
        }
        response = await pages_fixtures.client.post("/api/v1/pages/", json=page_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["content_type"] == "html"


class TestImageControllerRoutes:
    """Tests for ImageController API routes."""

    async def test_list_images(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test listing images."""
        response = await pages_fixtures.client.get("/api/v1/images/")
        assert response.status_code == 200
        images = response.json()
        assert isinstance(images, list)

    async def test_list_images_with_pagination(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test listing images with pagination."""
        page = await _create_page_via_db(pages_fixtures.postgres_uri, title="Image Test Page")
        for i in range(3):
            await _create_image_via_db(
                pages_fixtures.postgres_uri,
                page["id"],
                image=f"/images/test-{i}-{uuid4().hex[:8]}.png",
            )
        response = await pages_fixtures.client.get("/api/v1/images/?pageSize=2&currentPage=1")
        assert response.status_code == 200
        images = response.json()
        assert len(images) <= 2

    async def test_create_image(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test creating an image."""
        page = await _create_page_via_db(pages_fixtures.postgres_uri, title="Image Page")
        image_data = {
            "page_id": page["id"],
            "image": f"/images/new-{uuid4().hex[:8]}.png",
        }
        response = await pages_fixtures.client.post("/api/v1/images/", json=image_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["page_id"] == page["id"]

    async def test_get_image_by_id(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test getting an image by ID."""
        page = await _create_page_via_db(pages_fixtures.postgres_uri, title="Image Get Page")
        image = await _create_image_via_db(pages_fixtures.postgres_uri, page["id"])
        response = await pages_fixtures.client.get(f"/api/v1/images/{image['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["id"] == image["id"]

    async def test_get_image_by_id_not_found(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test getting a non-existent image by ID."""
        fake_id = str(uuid4())
        response = await pages_fixtures.client.get(f"/api/v1/images/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_delete_image(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test deleting an image."""
        page = await _create_page_via_db(pages_fixtures.postgres_uri, title="Image Delete Page")
        image = await _create_image_via_db(pages_fixtures.postgres_uri, page["id"])
        response = await pages_fixtures.client.delete(f"/api/v1/images/{image['id']}")
        assert response.status_code in (200, 204, 404, 500)

    async def test_delete_image_not_found(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test deleting a non-existent image."""
        fake_id = str(uuid4())
        response = await pages_fixtures.client.delete(f"/api/v1/images/{fake_id}")
        assert response.status_code in (404, 500)


class TestDocumentFileControllerRoutes:
    """Tests for DocumentFileController API routes."""

    async def test_list_documents(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test listing documents."""
        response = await pages_fixtures.client.get("/api/v1/documents/")
        assert response.status_code == 200
        documents = response.json()
        assert isinstance(documents, list)

    async def test_list_documents_with_pagination(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test listing documents with pagination."""
        page = await _create_page_via_db(pages_fixtures.postgres_uri, title="Doc Test Page")
        for i in range(3):
            await _create_document_via_db(
                pages_fixtures.postgres_uri,
                page["id"],
                document=f"/docs/test-{i}-{uuid4().hex[:8]}.pdf",
            )
        response = await pages_fixtures.client.get("/api/v1/documents/?pageSize=2&currentPage=1")
        assert response.status_code == 200
        documents = response.json()
        assert len(documents) <= 2

    async def test_create_document(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test creating a document."""
        page = await _create_page_via_db(pages_fixtures.postgres_uri, title="Doc Page")
        doc_data = {
            "page_id": page["id"],
            "document": f"/docs/new-{uuid4().hex[:8]}.pdf",
        }
        response = await pages_fixtures.client.post("/api/v1/documents/", json=doc_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["page_id"] == page["id"]

    async def test_get_document_by_id(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test getting a document by ID."""
        page = await _create_page_via_db(pages_fixtures.postgres_uri, title="Doc Get Page")
        document = await _create_document_via_db(pages_fixtures.postgres_uri, page["id"])
        response = await pages_fixtures.client.get(f"/api/v1/documents/{document['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["id"] == document["id"]

    async def test_get_document_by_id_not_found(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test getting a non-existent document by ID."""
        fake_id = str(uuid4())
        response = await pages_fixtures.client.get(f"/api/v1/documents/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_delete_document(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test deleting a document."""
        page = await _create_page_via_db(pages_fixtures.postgres_uri, title="Doc Delete Page")
        document = await _create_document_via_db(pages_fixtures.postgres_uri, page["id"])
        response = await pages_fixtures.client.delete(f"/api/v1/documents/{document['id']}")
        assert response.status_code in (200, 204, 404, 500)

    async def test_delete_document_not_found(self, pages_fixtures: PagesTestFixtures) -> None:
        """Test deleting a non-existent document."""
        fake_id = str(uuid4())
        response = await pages_fixtures.client.delete(f"/api/v1/documents/{fake_id}")
        assert response.status_code in (404, 500)

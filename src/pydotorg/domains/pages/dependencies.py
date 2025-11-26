"""Pages domain dependency injection providers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.domains.pages.repositories import DocumentFileRepository, ImageRepository, PageRepository
from pydotorg.domains.pages.services import DocumentFileService, ImageService, PageService


async def provide_page_repository(db_session: AsyncSession) -> PageRepository:
    """Provide a PageRepository instance."""
    return PageRepository(session=db_session)


async def provide_page_service(db_session: AsyncSession) -> PageService:
    """Provide a PageService instance."""
    return PageService(session=db_session)


async def provide_image_repository(db_session: AsyncSession) -> ImageRepository:
    """Provide an ImageRepository instance."""
    return ImageRepository(session=db_session)


async def provide_image_service(db_session: AsyncSession) -> ImageService:
    """Provide an ImageService instance."""
    return ImageService(session=db_session)


async def provide_document_file_repository(db_session: AsyncSession) -> DocumentFileRepository:
    """Provide a DocumentFileRepository instance."""
    return DocumentFileRepository(session=db_session)


async def provide_document_file_service(db_session: AsyncSession) -> DocumentFileService:
    """Provide a DocumentFileService instance."""
    return DocumentFileService(session=db_session)


def get_page_dependencies() -> dict:
    """Get all pages domain dependency providers."""
    return {
        "page_repository": provide_page_repository,
        "page_service": provide_page_service,
        "image_repository": provide_image_repository,
        "image_service": provide_image_service,
        "document_file_repository": provide_document_file_repository,
        "document_file_service": provide_document_file_service,
    }

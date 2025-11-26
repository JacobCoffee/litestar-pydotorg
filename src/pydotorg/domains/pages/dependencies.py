"""Pages domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.pages.repositories import DocumentFileRepository, ImageRepository, PageRepository
from pydotorg.domains.pages.services import DocumentFileService, ImageService, PageService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_page_repository(db_session: AsyncSession) -> AsyncGenerator[PageRepository, None]:
    """Provide a PageRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A PageRepository instance.
    """
    async with PageRepository(session=db_session) as repo:
        yield repo


async def provide_page_service(
    page_repository: PageRepository,
) -> AsyncGenerator[PageService, None]:
    """Provide a PageService instance.

    Args:
        page_repository: The page repository.

    Yields:
        A PageService instance.
    """
    async with PageService(repository=page_repository) as service:
        yield service


async def provide_image_repository(db_session: AsyncSession) -> AsyncGenerator[ImageRepository, None]:
    """Provide an ImageRepository instance.

    Args:
        db_session: The database session.

    Yields:
        An ImageRepository instance.
    """
    async with ImageRepository(session=db_session) as repo:
        yield repo


async def provide_image_service(
    image_repository: ImageRepository,
) -> AsyncGenerator[ImageService, None]:
    """Provide an ImageService instance.

    Args:
        image_repository: The image repository.

    Yields:
        An ImageService instance.
    """
    async with ImageService(repository=image_repository) as service:
        yield service


async def provide_document_file_repository(
    db_session: AsyncSession,
) -> AsyncGenerator[DocumentFileRepository, None]:
    """Provide a DocumentFileRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A DocumentFileRepository instance.
    """
    async with DocumentFileRepository(session=db_session) as repo:
        yield repo


async def provide_document_file_service(
    document_file_repository: DocumentFileRepository,
) -> AsyncGenerator[DocumentFileService, None]:
    """Provide a DocumentFileService instance.

    Args:
        document_file_repository: The document file repository.

    Yields:
        A DocumentFileService instance.
    """
    async with DocumentFileService(repository=document_file_repository) as service:
        yield service


def get_page_dependencies() -> dict:
    """Get all pages domain dependency providers.

    Returns:
        Dictionary of dependency providers for the pages domain.
    """
    return {
        "page_repository": provide_page_repository,
        "page_service": provide_page_service,
        "image_repository": provide_image_repository,
        "image_service": provide_image_service,
        "document_file_repository": provide_document_file_repository,
        "document_file_service": provide_document_file_service,
    }

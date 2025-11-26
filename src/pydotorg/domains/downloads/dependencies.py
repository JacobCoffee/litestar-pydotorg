"""Downloads domain dependency injection providers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.domains.downloads.repositories import OSRepository, ReleaseFileRepository, ReleaseRepository
from pydotorg.domains.downloads.services import OSService, ReleaseFileService, ReleaseService


async def provide_os_repository(db_session: AsyncSession) -> OSRepository:
    """Provide an OSRepository instance."""
    return OSRepository(session=db_session)


async def provide_os_service(db_session: AsyncSession) -> OSService:
    """Provide an OSService instance."""
    return OSService(session=db_session)


async def provide_release_repository(db_session: AsyncSession) -> ReleaseRepository:
    """Provide a ReleaseRepository instance."""
    return ReleaseRepository(session=db_session)


async def provide_release_service(db_session: AsyncSession) -> ReleaseService:
    """Provide a ReleaseService instance."""
    return ReleaseService(session=db_session)


async def provide_release_file_repository(db_session: AsyncSession) -> ReleaseFileRepository:
    """Provide a ReleaseFileRepository instance."""
    return ReleaseFileRepository(session=db_session)


async def provide_release_file_service(db_session: AsyncSession) -> ReleaseFileService:
    """Provide a ReleaseFileService instance."""
    return ReleaseFileService(session=db_session)


def get_downloads_dependencies() -> dict:
    """Get all downloads domain dependency providers."""
    return {
        "os_repository": provide_os_repository,
        "os_service": provide_os_service,
        "release_repository": provide_release_repository,
        "release_service": provide_release_service,
        "release_file_repository": provide_release_file_repository,
        "release_file_service": provide_release_file_service,
    }

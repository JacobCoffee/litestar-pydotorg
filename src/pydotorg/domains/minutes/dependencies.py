"""Minutes domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.minutes.repositories import MinutesRepository
from pydotorg.domains.minutes.services import MinutesService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_minutes_repository(db_session: AsyncSession) -> AsyncGenerator[MinutesRepository, None]:
    """Provide a MinutesRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A MinutesRepository instance.
    """
    async with MinutesRepository(session=db_session) as repo:
        yield repo


async def provide_minutes_service(
    minutes_repository: MinutesRepository,
) -> AsyncGenerator[MinutesService, None]:
    """Provide a MinutesService instance.

    Args:
        minutes_repository: The minutes repository.

    Yields:
        A MinutesService instance.
    """
    async with MinutesService(repository=minutes_repository) as service:
        yield service


def get_minutes_dependencies() -> dict:
    """Get all minutes domain dependency providers.

    Returns:
        Dictionary of dependency providers for the minutes domain.
    """
    return {
        "minutes_repository": provide_minutes_repository,
        "minutes_service": provide_minutes_service,
    }

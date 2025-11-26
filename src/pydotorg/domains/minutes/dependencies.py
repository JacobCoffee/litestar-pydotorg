"""Minutes domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.minutes.repositories import MinutesRepository
from pydotorg.domains.minutes.services import MinutesService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_minutes_repository(db_session: AsyncSession) -> MinutesRepository:
    """Provide a MinutesRepository instance."""
    return MinutesRepository(session=db_session)


async def provide_minutes_service(db_session: AsyncSession) -> MinutesService:
    """Provide a MinutesService instance."""
    return MinutesService(session=db_session)


def get_minutes_dependencies() -> dict:
    """Get all minutes domain dependency providers."""
    return {
        "minutes_repository": provide_minutes_repository,
        "minutes_service": provide_minutes_service,
    }

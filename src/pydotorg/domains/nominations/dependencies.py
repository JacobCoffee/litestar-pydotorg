"""Nominations domain dependency injection providers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.domains.nominations.repositories import (
    ElectionRepository,
    NominationRepository,
    NomineeRepository,
)
from pydotorg.domains.nominations.services import (
    ElectionService,
    NominationService,
    NomineeService,
)


async def provide_election_repository(db_session: AsyncSession) -> ElectionRepository:
    """Provide an ElectionRepository instance."""
    return ElectionRepository(session=db_session)


async def provide_election_service(db_session: AsyncSession) -> ElectionService:
    """Provide an ElectionService instance."""
    return ElectionService(session=db_session)


async def provide_nominee_repository(db_session: AsyncSession) -> NomineeRepository:
    """Provide a NomineeRepository instance."""
    return NomineeRepository(session=db_session)


async def provide_nominee_service(db_session: AsyncSession) -> NomineeService:
    """Provide a NomineeService instance."""
    return NomineeService(session=db_session)


async def provide_nomination_repository(db_session: AsyncSession) -> NominationRepository:
    """Provide a NominationRepository instance."""
    return NominationRepository(session=db_session)


async def provide_nomination_service(db_session: AsyncSession) -> NominationService:
    """Provide a NominationService instance."""
    return NominationService(session=db_session)


def get_nominations_dependencies() -> dict:
    """Get all nominations domain dependency providers."""
    return {
        "election_repository": provide_election_repository,
        "election_service": provide_election_service,
        "nominee_repository": provide_nominee_repository,
        "nominee_service": provide_nominee_service,
        "nomination_repository": provide_nomination_repository,
        "nomination_service": provide_nomination_service,
    }

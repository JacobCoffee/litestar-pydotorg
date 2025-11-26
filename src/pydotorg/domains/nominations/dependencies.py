"""Nominations domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_election_repository(db_session: AsyncSession) -> AsyncGenerator[ElectionRepository, None]:
    """Provide an ElectionRepository instance.

    Args:
        db_session: The database session.

    Yields:
        An ElectionRepository instance.
    """
    async with ElectionRepository(session=db_session) as repo:
        yield repo


async def provide_election_service(
    election_repository: ElectionRepository,
) -> AsyncGenerator[ElectionService, None]:
    """Provide an ElectionService instance.

    Args:
        election_repository: The election repository.

    Yields:
        An ElectionService instance.
    """
    async with ElectionService(repository=election_repository) as service:
        yield service


async def provide_nominee_repository(db_session: AsyncSession) -> AsyncGenerator[NomineeRepository, None]:
    """Provide a NomineeRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A NomineeRepository instance.
    """
    async with NomineeRepository(session=db_session) as repo:
        yield repo


async def provide_nominee_service(
    nominee_repository: NomineeRepository,
) -> AsyncGenerator[NomineeService, None]:
    """Provide a NomineeService instance.

    Args:
        nominee_repository: The nominee repository.

    Yields:
        A NomineeService instance.
    """
    async with NomineeService(repository=nominee_repository) as service:
        yield service


async def provide_nomination_repository(db_session: AsyncSession) -> AsyncGenerator[NominationRepository, None]:
    """Provide a NominationRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A NominationRepository instance.
    """
    async with NominationRepository(session=db_session) as repo:
        yield repo


async def provide_nomination_service(
    nomination_repository: NominationRepository,
) -> AsyncGenerator[NominationService, None]:
    """Provide a NominationService instance.

    Args:
        nomination_repository: The nomination repository.

    Yields:
        A NominationService instance.
    """
    async with NominationService(repository=nomination_repository) as service:
        yield service


def get_nominations_dependencies() -> dict:
    """Get all nominations domain dependency providers.

    Returns:
        Dictionary of dependency providers for the nominations domain.
    """
    return {
        "election_repository": provide_election_repository,
        "election_service": provide_election_service,
        "nominee_repository": provide_nominee_repository,
        "nominee_service": provide_nominee_service,
        "nomination_repository": provide_nomination_repository,
        "nomination_service": provide_nomination_service,
    }

"""Sponsors domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.sponsors.repositories import (
    ContractRepository,
    LegalClauseRepository,
    SponsorRepository,
    SponsorshipLevelRepository,
    SponsorshipRepository,
)
from pydotorg.domains.sponsors.services import (
    ContractService,
    LegalClauseService,
    SponsorService,
    SponsorshipLevelService,
    SponsorshipService,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_sponsorship_level_repository(db_session: AsyncSession) -> SponsorshipLevelRepository:
    """Provide a SponsorshipLevelRepository instance."""
    return SponsorshipLevelRepository(session=db_session)


async def provide_sponsorship_level_service(db_session: AsyncSession) -> SponsorshipLevelService:
    """Provide a SponsorshipLevelService instance."""
    return SponsorshipLevelService(session=db_session)


async def provide_sponsor_repository(db_session: AsyncSession) -> SponsorRepository:
    """Provide a SponsorRepository instance."""
    return SponsorRepository(session=db_session)


async def provide_sponsor_service(db_session: AsyncSession) -> SponsorService:
    """Provide a SponsorService instance."""
    return SponsorService(session=db_session)


async def provide_sponsorship_repository(db_session: AsyncSession) -> SponsorshipRepository:
    """Provide a SponsorshipRepository instance."""
    return SponsorshipRepository(session=db_session)


async def provide_sponsorship_service(db_session: AsyncSession) -> SponsorshipService:
    """Provide a SponsorshipService instance."""
    return SponsorshipService(session=db_session)


async def provide_legal_clause_repository(db_session: AsyncSession) -> LegalClauseRepository:
    """Provide a LegalClauseRepository instance."""
    return LegalClauseRepository(session=db_session)


async def provide_legal_clause_service(db_session: AsyncSession) -> LegalClauseService:
    """Provide a LegalClauseService instance."""
    return LegalClauseService(session=db_session)


async def provide_contract_repository(db_session: AsyncSession) -> ContractRepository:
    """Provide a ContractRepository instance."""
    return ContractRepository(session=db_session)


async def provide_contract_service(db_session: AsyncSession) -> ContractService:
    """Provide a ContractService instance."""
    return ContractService(session=db_session)


def get_sponsors_dependencies() -> dict:
    """Get all sponsors domain dependency providers."""
    return {
        "sponsorship_level_repository": provide_sponsorship_level_repository,
        "sponsorship_level_service": provide_sponsorship_level_service,
        "sponsor_repository": provide_sponsor_repository,
        "sponsor_service": provide_sponsor_service,
        "sponsorship_repository": provide_sponsorship_repository,
        "sponsorship_service": provide_sponsorship_service,
        "legal_clause_repository": provide_legal_clause_repository,
        "legal_clause_service": provide_legal_clause_service,
        "contract_repository": provide_contract_repository,
        "contract_service": provide_contract_service,
    }

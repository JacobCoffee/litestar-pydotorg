"""Banners domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.banners.repositories import BannerRepository
from pydotorg.domains.banners.services import BannerService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_banner_repository(db_session: AsyncSession) -> AsyncGenerator[BannerRepository, None]:
    """Provide a BannerRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A BannerRepository instance.
    """
    async with BannerRepository(session=db_session) as repo:
        yield repo


async def provide_banner_service(
    banner_repository: BannerRepository,
) -> AsyncGenerator[BannerService, None]:
    """Provide a BannerService instance.

    Args:
        banner_repository: The banner repository.

    Yields:
        A BannerService instance.
    """
    async with BannerService(repository=banner_repository) as service:
        yield service


def get_banners_dependencies() -> dict:
    """Get all banners domain dependency providers.

    Returns:
        Dictionary of dependency providers for the banners domain.
    """
    return {
        "banner_repository": provide_banner_repository,
        "banner_service": provide_banner_service,
    }

"""Banners domain dependency injection providers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.domains.banners.repositories import BannerRepository
from pydotorg.domains.banners.services import BannerService


async def provide_banner_repository(db_session: AsyncSession) -> BannerRepository:
    """Provide a BannerRepository instance."""
    return BannerRepository(session=db_session)


async def provide_banner_service(db_session: AsyncSession) -> BannerService:
    """Provide a BannerService instance."""
    return BannerService(session=db_session)


def get_banners_dependencies() -> dict:
    """Get all banners domain dependency providers."""
    return {
        "banner_repository": provide_banner_repository,
        "banner_service": provide_banner_service,
    }

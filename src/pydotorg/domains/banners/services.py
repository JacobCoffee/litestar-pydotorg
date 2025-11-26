"""Banners domain services for business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from pydotorg.domains.banners.models import Banner
from pydotorg.domains.banners.repositories import BannerRepository

if TYPE_CHECKING:
    import datetime


class BannerService(SQLAlchemyAsyncRepositoryService[Banner]):
    """Service for Banner business logic."""

    repository_type = BannerRepository

    async def get_active_banners(self, current_date: datetime.date | None = None) -> list[Banner]:
        """Get active banners.

        Args:
            current_date: The date to check against. If None, only checks is_active flag.

        Returns:
            List of active banners.
        """
        return await self.repository.get_active_banners(current_date=current_date)

    async def get_by_name(self, name: str) -> Banner | None:
        """Get a banner by name.

        Args:
            name: The banner name to search for.

        Returns:
            The banner if found, None otherwise.
        """
        return await self.repository.get_by_name(name)

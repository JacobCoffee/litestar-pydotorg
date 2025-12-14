"""Banners domain repositories for database access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import or_, select

from pydotorg.domains.banners.models import Banner

if TYPE_CHECKING:
    import datetime


class BannerRepository(SQLAlchemyAsyncRepository[Banner]):
    """Repository for Banner database operations."""

    model_type = Banner

    async def get_active_banners(self, current_date: datetime.date | None = None) -> list[Banner]:
        """Get active banners.

        Args:
            current_date: The date to check against. If None, only checks is_active flag.

        Returns:
            List of active banners.
        """
        if current_date is None:
            statement = select(Banner).where(Banner.is_active.is_(True))
        else:
            statement = select(Banner).where(
                Banner.is_active.is_(True),
                (Banner.start_date.is_(None)) | (Banner.start_date <= current_date),
                (Banner.end_date.is_(None)) | (Banner.end_date >= current_date),
            )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_sitewide_banners(self, current_date: datetime.date | None = None) -> list[Banner]:
        """Get active sitewide banners (is_sitewide=True).

        Args:
            current_date: The date to check against. If None, only checks is_active flag.

        Returns:
            List of active sitewide banners.
        """
        if current_date is None:
            statement = select(Banner).where(Banner.is_active.is_(True), Banner.is_sitewide.is_(True))
        else:
            statement = select(Banner).where(
                Banner.is_active.is_(True),
                Banner.is_sitewide.is_(True),
                (Banner.start_date.is_(None)) | (Banner.start_date <= current_date),
                (Banner.end_date.is_(None)) | (Banner.end_date >= current_date),
            )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_frontend_banners(self, current_date: datetime.date | None = None) -> list[Banner]:
        """Get active banners for frontend pages (sitewide OR target=frontend).

        Args:
            current_date: The date to check against. If None, only checks is_active flag.

        Returns:
            List of active frontend banners.
        """
        if current_date is None:
            statement = select(Banner).where(
                Banner.is_active.is_(True),
                or_(Banner.is_sitewide.is_(True), Banner.target == "frontend"),
            )
        else:
            statement = select(Banner).where(
                Banner.is_active.is_(True),
                or_(Banner.is_sitewide.is_(True), Banner.target == "frontend"),
                (Banner.start_date.is_(None)) | (Banner.start_date <= current_date),
                (Banner.end_date.is_(None)) | (Banner.end_date >= current_date),
            )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_api_banners(self, current_date: datetime.date | None = None) -> list[Banner]:
        """Get active banners for API routes (sitewide OR target=api).

        Args:
            current_date: The date to check against. If None, only checks is_active flag.

        Returns:
            List of active API banners.
        """
        if current_date is None:
            statement = select(Banner).where(
                Banner.is_active.is_(True),
                or_(Banner.is_sitewide.is_(True), Banner.target == "api"),
            )
        else:
            statement = select(Banner).where(
                Banner.is_active.is_(True),
                or_(Banner.is_sitewide.is_(True), Banner.target == "api"),
                (Banner.start_date.is_(None)) | (Banner.start_date <= current_date),
                (Banner.end_date.is_(None)) | (Banner.end_date >= current_date),
            )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Banner | None:
        """Get a banner by name.

        Args:
            name: The banner name to search for.

        Returns:
            The banner if found, None otherwise.
        """
        statement = select(Banner).where(Banner.name == name)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

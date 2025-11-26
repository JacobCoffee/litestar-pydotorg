"""Downloads domain repositories for database access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from pydotorg.domains.downloads.models import OS, PythonVersion, Release, ReleaseFile

if TYPE_CHECKING:
    from uuid import UUID


class OSRepository(SQLAlchemyAsyncRepository[OS]):
    """Repository for OS database operations."""

    model_type = OS

    async def get_by_slug(self, slug: str) -> OS | None:
        """Get an OS by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The OS if found, None otherwise.
        """
        statement = select(OS).where(OS.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()


class ReleaseRepository(SQLAlchemyAsyncRepository[Release]):
    """Repository for Release database operations."""

    model_type = Release

    async def get_by_slug(self, slug: str) -> Release | None:
        """Get a release by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The release if found, None otherwise.
        """
        statement = select(Release).where(Release.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_latest(self, version: PythonVersion = PythonVersion.PYTHON3) -> Release | None:
        """Get the latest stable release for a Python version.

        Args:
            version: The Python version to search for.

        Returns:
            The latest release if found, None otherwise.
        """
        statement = (
            select(Release)
            .where(
                Release.version == version,
                Release.is_published.is_(True),
                Release.is_latest.is_(True),
            )
            .order_by(Release.release_date.desc())
            .limit(1)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_published(self, limit: int = 100, offset: int = 0) -> list[Release]:
        """Get all published releases.

        Args:
            limit: Maximum number of releases to return.
            offset: Number of releases to skip.

        Returns:
            List of published releases ordered by release date descending.
        """
        statement = (
            select(Release)
            .where(Release.is_published.is_(True))
            .order_by(Release.release_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_for_download_page(self, limit: int = 100) -> list[Release]:
        """Get releases marked to show on the download page.

        Args:
            limit: Maximum number of releases to return.

        Returns:
            List of releases for download page ordered by release date descending.
        """
        statement = (
            select(Release)
            .where(
                Release.is_published.is_(True),
                Release.show_on_download_page.is_(True),
            )
            .order_by(Release.release_date.desc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_version(self, version: PythonVersion, limit: int = 100) -> list[Release]:
        """Get all releases for a specific Python version.

        Args:
            version: The Python version to filter by.
            limit: Maximum number of releases to return.

        Returns:
            List of releases for the specified version.
        """
        statement = (
            select(Release)
            .where(Release.version == version, Release.is_published.is_(True))
            .order_by(Release.release_date.desc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class ReleaseFileRepository(SQLAlchemyAsyncRepository[ReleaseFile]):
    """Repository for ReleaseFile database operations."""

    model_type = ReleaseFile

    async def get_by_release_id(self, release_id: UUID) -> list[ReleaseFile]:
        """Get all files for a specific release.

        Args:
            release_id: The release ID to search for.

        Returns:
            List of release files.
        """
        statement = select(ReleaseFile).where(ReleaseFile.release_id == release_id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_os_id(self, os_id: UUID, limit: int = 100) -> list[ReleaseFile]:
        """Get all files for a specific OS.

        Args:
            os_id: The OS ID to search for.
            limit: Maximum number of files to return.

        Returns:
            List of release files.
        """
        statement = select(ReleaseFile).where(ReleaseFile.os_id == os_id).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> ReleaseFile | None:
        """Get a release file by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The release file if found, None otherwise.
        """
        statement = select(ReleaseFile).where(ReleaseFile.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_source_files(self, release_id: UUID) -> list[ReleaseFile]:
        """Get all source files for a release.

        Args:
            release_id: The release ID to search for.

        Returns:
            List of source release files.
        """
        statement = select(ReleaseFile).where(
            ReleaseFile.release_id == release_id,
            ReleaseFile.is_source.is_(True),
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

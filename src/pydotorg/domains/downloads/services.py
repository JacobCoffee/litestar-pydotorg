"""Downloads domain services for business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from pydotorg.domains.downloads.models import OS, PythonVersion, Release, ReleaseFile
from pydotorg.domains.downloads.repositories import OSRepository, ReleaseFileRepository, ReleaseRepository

if TYPE_CHECKING:
    from uuid import UUID


class OSService(SQLAlchemyAsyncRepositoryService[OS]):
    """Service for OS business logic."""

    repository_type = OSRepository
    match_fields = ["slug"]

    async def get_by_slug(self, slug: str) -> OS | None:
        """Get an OS by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The OS if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)


class ReleaseService(SQLAlchemyAsyncRepositoryService[Release]):
    """Service for Release business logic."""

    repository_type = ReleaseRepository
    match_fields = ["slug"]

    async def get_by_slug(self, slug: str) -> Release | None:
        """Get a release by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The release if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def get_latest(self, version: PythonVersion = PythonVersion.PYTHON3) -> Release | None:
        """Get the latest stable release for a Python version.

        Args:
            version: The Python version to search for.

        Returns:
            The latest release if found, None otherwise.
        """
        return await self.repository.get_latest(version)

    async def get_published(self, limit: int = 100, offset: int = 0) -> list[Release]:
        """Get all published releases.

        Args:
            limit: Maximum number of releases to return.
            offset: Number of releases to skip.

        Returns:
            List of published releases.
        """
        return await self.repository.get_published(limit=limit, offset=offset)

    async def get_for_download_page(self, limit: int = 100) -> list[Release]:
        """Get releases marked to show on the download page.

        Args:
            limit: Maximum number of releases to return.

        Returns:
            List of releases for download page.
        """
        return await self.repository.get_for_download_page(limit=limit)

    async def get_by_version(self, version: PythonVersion, limit: int = 100) -> list[Release]:
        """Get all releases for a specific Python version.

        Args:
            version: The Python version to filter by.
            limit: Maximum number of releases to return.

        Returns:
            List of releases for the specified version.
        """
        return await self.repository.get_by_version(version, limit=limit)

    async def get_files_grouped_by_os(self, release_id: UUID) -> dict[str, list[ReleaseFile]]:
        """Get release files grouped by OS slug.

        Args:
            release_id: The release ID to get files for.

        Returns:
            Dictionary mapping OS slug to list of release files.
        """
        release = await self.get(release_id)
        if not release:
            return {}

        files_by_os: dict[str, list[ReleaseFile]] = {}
        for file in release.files:
            os_slug = file.os.slug
            if os_slug not in files_by_os:
                files_by_os[os_slug] = []
            files_by_os[os_slug].append(file)

        return files_by_os

    async def get_releases_grouped_by_minor_version(self, limit: int = 500) -> dict[str, dict[str, list[Release]]]:
        """Get releases grouped by major and then minor version.

        Returns a nested dict structure::

            {
                "3": {
                    "3.14": [releases...],
                    "3.13": [releases...],
                    ...
                },
                "2": {
                    "2.7": [releases...],
                }
            }

        Args:
            limit: Maximum number of releases to fetch.

        Returns:
            Nested dictionary mapping major version -> minor version -> releases.
        """
        releases = await self.repository.get_for_download_page(limit=limit)

        grouped: dict[str, dict[str, list[Release]]] = {}
        for release in releases:
            major = release.major_version
            minor = release.minor_version

            if major not in grouped:
                grouped[major] = {}
            if minor not in grouped[major]:
                grouped[major][minor] = []

            grouped[major][minor].append(release)

        sorted_grouped: dict[str, dict[str, list[Release]]] = {}
        for major in sorted(grouped.keys(), key=lambda x: (0 if x.isdigit() else 1, -int(x) if x.isdigit() else x)):
            sorted_grouped[major] = {}
            for minor in sorted(
                grouped[major].keys(),
                key=lambda x: tuple(-int(p) if p.isdigit() else 0 for p in x.split(".")),
            ):
                sorted_grouped[major][minor] = grouped[major][minor]

        return sorted_grouped

    async def mark_as_latest(self, release_id: UUID, version: PythonVersion) -> Release:
        """Mark a release as the latest for its Python version.

        This will unmark any other releases as latest for the same version.

        Args:
            release_id: The release ID to mark as latest.
            version: The Python version.

        Returns:
            The updated release instance.
        """
        all_releases = await self.repository.get_by_version(version, limit=1000)
        for release in all_releases:
            if release.id == release_id:
                release.is_latest = True
            else:
                release.is_latest = False
            await self.repository.update(release)

        return await self.get(release_id)


class ReleaseFileService(SQLAlchemyAsyncRepositoryService[ReleaseFile]):
    """Service for ReleaseFile business logic."""

    repository_type = ReleaseFileRepository
    match_fields = ["slug"]

    async def get_by_release_id(self, release_id: UUID) -> list[ReleaseFile]:
        """Get all files for a specific release.

        Args:
            release_id: The release ID to search for.

        Returns:
            List of release files.
        """
        return await self.repository.get_by_release_id(release_id)

    async def get_by_os_id(self, os_id: UUID, limit: int = 100) -> list[ReleaseFile]:
        """Get all files for a specific OS.

        Args:
            os_id: The OS ID to search for.
            limit: Maximum number of files to return.

        Returns:
            List of release files.
        """
        return await self.repository.get_by_os_id(os_id, limit=limit)

    async def get_by_slug(self, slug: str) -> ReleaseFile | None:
        """Get a release file by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The release file if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def get_source_files(self, release_id: UUID) -> list[ReleaseFile]:
        """Get all source files for a release.

        Args:
            release_id: The release ID to search for.

        Returns:
            List of source release files.
        """
        return await self.repository.get_source_files(release_id)

    async def get_download_button_file(self, release_id: UUID, os_id: UUID) -> ReleaseFile | None:
        """Get the download button file for a release and OS.

        Args:
            release_id: The release ID.
            os_id: The OS ID.

        Returns:
            The release file marked as download button, None if not found.
        """
        files = await self.get_by_release_id(release_id)
        for file in files:
            if file.os_id == os_id and file.download_button:
                return file
        return None

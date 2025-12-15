"""Downloads domain API and page controllers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Body, Parameter
from litestar.response import Template
from litestar.stores.redis import RedisStore

from pydotorg.domains.downloads.models import PythonVersion
from pydotorg.domains.downloads.schemas import (
    OSCreate,
    OSRead,
    ReleaseCreate,
    ReleaseFileCreate,
    ReleaseFileRead,
    ReleaseList,
    ReleaseRead,
    ReleaseUpdate,
)
from pydotorg.domains.downloads.services import OSService, ReleaseFileService, ReleaseService
from pydotorg.tasks.downloads import DownloadStatsService

if TYPE_CHECKING:
    from litestar import Request

logger = logging.getLogger(__name__)


class OSController(Controller):
    """Controller for OS CRUD operations."""

    path = "/api/v1/os"
    tags = ["Downloads"]

    @get("/")
    async def list_os(
        self,
        os_service: OSService,
        limit_offset: LimitOffset,
    ) -> list[OSRead]:
        """List all operating systems with pagination.

        Retrieves a paginated list of supported operating systems for Python
        downloads (e.g., Windows, macOS, Linux).

        Args:
            os_service: Service for operating system database operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of supported operating systems with their details.
        """
        os_list, _total = await os_service.list_and_count(limit_offset)
        return [OSRead.model_validate(os) for os in os_list]

    @get("/{os_id:uuid}")
    async def get_os(
        self,
        os_service: OSService,
        os_id: Annotated[UUID, Parameter(title="OS ID", description="The OS ID")],
    ) -> OSRead:
        """Retrieve a specific operating system by its unique identifier.

        Fetches complete OS information including name, slug, and display
        configuration.

        Args:
            os_service: Service for operating system database operations.
            os_id: The unique UUID identifier of the operating system.

        Returns:
            Complete operating system details.

        Raises:
            NotFoundException: If no OS with the given ID exists.
        """
        os = await os_service.get(os_id)
        return OSRead.model_validate(os)

    @get("/slug/{slug:str}")
    async def get_os_by_slug(
        self,
        os_service: OSService,
        slug: Annotated[str, Parameter(title="Slug", description="The OS slug")],
    ) -> OSRead:
        """Look up an operating system by its URL slug.

        Searches for an OS with the specified slug (e.g., "windows", "macos",
        "linux") and returns its details.

        Args:
            os_service: Service for operating system database operations.
            slug: The URL-friendly slug identifier.

        Returns:
            Complete operating system details.

        Raises:
            NotFoundException: If no OS with the given slug exists.
        """
        os = await os_service.get_by_slug(slug)
        if not os:
            raise NotFoundException(f"OS with slug {slug} not found")
        return OSRead.model_validate(os)

    @post("/")
    async def create_os(
        self,
        os_service: OSService,
        data: Annotated[OSCreate, Body(title="O S", description="Operating system to create")],
    ) -> OSRead:
        """Create a new operating system entry.

        Adds a new supported operating system to the downloads system.
        Release files can then be associated with this OS.

        Args:
            os_service: Service for operating system database operations.
            data: Operating system creation payload with name and slug.

        Returns:
            The newly created operating system.

        Raises:
            ConflictError: If an OS with the same slug exists.
        """
        os = await os_service.create(data.model_dump())
        return OSRead.model_validate(os)

    @delete("/{os_id:uuid}")
    async def delete_os(
        self,
        os_service: OSService,
        os_id: Annotated[UUID, Parameter(title="OS ID", description="The OS ID")],
    ) -> None:
        """Delete an operating system entry.

        Permanently removes an OS from the system. Release files associated
        with this OS should be reassigned first.

        Args:
            os_service: Service for operating system database operations.
            os_id: The unique UUID identifier of the OS to delete.

        Raises:
            NotFoundException: If no OS with the given ID exists.
        """
        await os_service.delete(os_id)


class ReleaseController(Controller):
    """Controller for Release CRUD operations."""

    path = "/api/v1/releases"
    tags = ["Downloads"]

    @get("/")
    async def list_releases(
        self,
        release_service: ReleaseService,
        limit_offset: LimitOffset,
    ) -> list[ReleaseList]:
        """List all Python releases with pagination.

        Retrieves a paginated list of all Python releases including stable,
        pre-release, and archived versions.

        Args:
            release_service: Service for release database operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of releases with version and status information.
        """
        releases, _total = await release_service.list_and_count(limit_offset)
        return [ReleaseList.model_validate(release) for release in releases]

    @get("/{release_id:uuid}")
    async def get_release(
        self,
        release_service: ReleaseService,
        release_id: Annotated[UUID, Parameter(title="Release ID", description="The release ID")],
    ) -> ReleaseRead:
        """Retrieve a specific release by its unique identifier.

        Fetches complete release information including version number,
        release date, release notes, and download files.

        Args:
            release_service: Service for release database operations.
            release_id: The unique UUID identifier of the release.

        Returns:
            Complete release details with associated files.

        Raises:
            NotFoundException: If no release with the given ID exists.
        """
        release = await release_service.get(release_id)
        return ReleaseRead.model_validate(release)

    @get("/slug/{slug:str}")
    async def get_release_by_slug(
        self,
        release_service: ReleaseService,
        slug: Annotated[str, Parameter(title="Slug", description="The release slug")],
    ) -> ReleaseRead:
        """Look up a release by its URL slug.

        Searches for a release with the specified slug (e.g., "python-3.12.0")
        and returns its complete details.

        Args:
            release_service: Service for release database operations.
            slug: The URL-friendly slug identifier.

        Returns:
            Complete release details with associated files.

        Raises:
            NotFoundException: If no release with the given slug exists.
        """
        release = await release_service.get_by_slug(slug)
        if not release:
            raise NotFoundException(f"Release with slug {slug} not found")
        return ReleaseRead.model_validate(release)

    @get("/latest")
    async def get_latest_release(
        self,
        release_service: ReleaseService,
    ) -> ReleaseRead:
        """Get the latest stable Python 3 release.

        Retrieves the most recent stable Python 3.x release recommended
        for new users and production use.

        Args:
            release_service: Service for release database operations.

        Returns:
            The latest Python 3 release details.

        Raises:
            NotFoundException: If no Python 3 release exists.
        """
        release = await release_service.get_latest(PythonVersion.PYTHON3)
        if not release:
            raise NotFoundException("No latest release found")
        return ReleaseRead.model_validate(release)

    @get("/latest/{version:str}")
    async def get_latest_by_version(
        self,
        release_service: ReleaseService,
        version: Annotated[str, Parameter(title="Version", description="Python version (2, 3, etc.)")],
    ) -> ReleaseRead:
        """Get the latest release for a specific Python major version.

        Retrieves the most recent stable release for the specified Python
        major version series (e.g., Python 2.x or Python 3.x).

        Args:
            release_service: Service for release database operations.
            version: The Python major version ("2" or "3").

        Returns:
            The latest release for the specified Python version.

        Raises:
            NotFoundException: If the version is invalid or no release exists.
        """
        try:
            python_version = PythonVersion(version)
        except ValueError as exc:
            msg = f"Invalid Python version: {version}"
            raise NotFoundException(msg) from exc

        release = await release_service.get_latest(python_version)
        if not release:
            raise NotFoundException(f"No latest release found for Python {version}")
        return ReleaseRead.model_validate(release)

    @get("/published")
    async def list_published_releases(
        self,
        release_service: ReleaseService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[ReleaseList]:
        """List all publicly published Python releases.

        Retrieves releases that have been marked as published and are
        available for download. Excludes draft and hidden releases.

        Args:
            release_service: Service for release database operations.
            limit: Maximum number of releases to return (1-1000).
            offset: Number of releases to skip for pagination.

        Returns:
            List of published releases sorted by release date.
        """
        releases = await release_service.get_published(limit=limit, offset=offset)
        return [ReleaseList.model_validate(release) for release in releases]

    @get("/download-page")
    async def list_download_page_releases(
        self,
        release_service: ReleaseService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
    ) -> list[ReleaseList]:
        """List releases for the main downloads page.

        Retrieves releases that should be displayed on the public downloads
        page, filtered and sorted for optimal user experience.

        Args:
            release_service: Service for release database operations.
            limit: Maximum number of releases to return (1-1000).

        Returns:
            List of releases suitable for the downloads page.
        """
        releases = await release_service.get_for_download_page(limit=limit)
        return [ReleaseList.model_validate(release) for release in releases]

    @post("/")
    async def create_release(
        self,
        release_service: ReleaseService,
        data: Annotated[ReleaseCreate, Body(title="Release", description="Release to create")],
    ) -> ReleaseRead:
        """Create a new Python release.

        Creates a new release record with version information, release date,
        and release notes. Files can be added separately.

        Args:
            release_service: Service for release database operations.
            data: Release creation payload with version and metadata.

        Returns:
            The newly created release.

        Raises:
            ConflictError: If a release with the same slug exists.
        """
        release = await release_service.create(data.model_dump())
        return ReleaseRead.model_validate(release)

    @put("/{release_id:uuid}")
    async def update_release(
        self,
        release_service: ReleaseService,
        data: Annotated[ReleaseUpdate, Body(title="Release", description="Release data to update")],
        release_id: Annotated[UUID, Parameter(title="Release ID", description="The release ID")],
    ) -> ReleaseRead:
        """Update an existing release.

        Modifies release fields with the provided values. Can update
        release notes, publication status, and metadata.

        Args:
            release_service: Service for release database operations.
            data: Partial release update payload with fields to modify.
            release_id: The unique UUID identifier of the release to update.

        Returns:
            The updated release with all current fields.

        Raises:
            NotFoundException: If no release with the given ID exists.
        """
        update_data = data.model_dump(exclude_unset=True)
        release = await release_service.update(update_data, item_id=release_id)
        return ReleaseRead.model_validate(release)

    @delete("/{release_id:uuid}")
    async def delete_release(
        self,
        release_service: ReleaseService,
        release_id: Annotated[UUID, Parameter(title="Release ID", description="The release ID")],
    ) -> None:
        """Permanently delete a release.

        Removes a release and all associated download files from the system.
        This action is irreversible.

        Args:
            release_service: Service for release database operations.
            release_id: The unique UUID identifier of the release to delete.

        Raises:
            NotFoundException: If no release with the given ID exists.
        """
        await release_service.delete(release_id)


class ReleaseFileController(Controller):
    """Controller for ReleaseFile CRUD operations."""

    path = "/api/v1/files"
    tags = ["Downloads"]

    @get("/{file_id:uuid}")
    async def get_file(
        self,
        release_file_service: ReleaseFileService,
        file_id: Annotated[UUID, Parameter(title="File ID", description="The file ID")],
    ) -> ReleaseFileRead:
        """Retrieve a specific release file by its unique identifier.

        Fetches complete file information including filename, size, checksum,
        and download URL.

        Args:
            release_file_service: Service for release file database operations.
            file_id: The unique UUID identifier of the file.

        Returns:
            Complete release file details.

        Raises:
            NotFoundException: If no file with the given ID exists.
        """
        file = await release_file_service.get(file_id)
        return ReleaseFileRead.model_validate(file)

    @get("/release/{release_id:uuid}")
    async def list_files_by_release(
        self,
        release_file_service: ReleaseFileService,
        release_id: Annotated[UUID, Parameter(title="Release ID", description="The release ID")],
    ) -> list[ReleaseFileRead]:
        """List all download files for a specific release.

        Retrieves all available download files for a release, including
        installers, source archives, and documentation.

        Args:
            release_file_service: Service for release file database operations.
            release_id: The unique UUID identifier of the release.

        Returns:
            List of download files for the specified release.
        """
        files = await release_file_service.get_by_release_id(release_id)
        return [ReleaseFileRead.model_validate(file) for file in files]

    @get("/os/{os_id:uuid}")
    async def list_files_by_os(
        self,
        release_file_service: ReleaseFileService,
        os_id: Annotated[UUID, Parameter(title="OS ID", description="The OS ID")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
    ) -> list[ReleaseFileRead]:
        """List all download files for a specific operating system.

        Retrieves all available download files compatible with the specified
        OS across all releases.

        Args:
            release_file_service: Service for release file database operations.
            os_id: The unique UUID identifier of the operating system.
            limit: Maximum number of files to return (1-1000).

        Returns:
            List of download files for the specified OS.
        """
        files = await release_file_service.get_by_os_id(os_id, limit=limit)
        return [ReleaseFileRead.model_validate(file) for file in files]

    @get("/slug/{slug:str}")
    async def get_file_by_slug(
        self,
        release_file_service: ReleaseFileService,
        slug: Annotated[str, Parameter(title="Slug", description="The file slug")],
    ) -> ReleaseFileRead:
        """Look up a release file by its URL slug.

        Searches for a file with the specified slug and returns its
        download information.

        Args:
            release_file_service: Service for release file database operations.
            slug: The URL-friendly slug identifier.

        Returns:
            Complete release file details.

        Raises:
            NotFoundException: If no file with the given slug exists.
        """
        file = await release_file_service.get_by_slug(slug)
        if not file:
            raise NotFoundException(f"File with slug {slug} not found")
        return ReleaseFileRead.model_validate(file)

    @post("/")
    async def create_file(
        self,
        release_file_service: ReleaseFileService,
        data: Annotated[ReleaseFileCreate, Body(title="Release File", description="Release file to create")],
    ) -> ReleaseFileRead:
        """Create a new release file entry.

        Adds a new downloadable file to a release with filename, size,
        checksum, and download URL.

        Args:
            release_file_service: Service for release file database operations.
            data: Release file creation payload with file details.

        Returns:
            The newly created release file.

        Raises:
            NotFoundException: If the associated release does not exist.
        """
        file = await release_file_service.create(data.model_dump())
        return ReleaseFileRead.model_validate(file)

    @delete("/{file_id:uuid}")
    async def delete_file(
        self,
        release_file_service: ReleaseFileService,
        file_id: Annotated[UUID, Parameter(title="File ID", description="The file ID")],
    ) -> None:
        """Delete a release file entry.

        Permanently removes a download file entry from the system.
        This action is irreversible.

        Args:
            release_file_service: Service for release file database operations.
            file_id: The unique UUID identifier of the file to delete.

        Raises:
            NotFoundException: If no file with the given ID exists.
        """
        await release_file_service.delete(file_id)

    @post("/{file_id:uuid}/track")
    async def track_download(
        self,
        request: Request,
        release_file_service: ReleaseFileService,
        file_id: Annotated[UUID, Parameter(title="File ID", description="The file ID")],
    ) -> dict:
        """Track a download event for a release file.

        Records a download event in Redis for analytics tracking.
        This endpoint is typically called when a user clicks a download link.

        Args:
            request: The current HTTP request.
            release_file_service: Service for release file database operations.
            file_id: The unique UUID identifier of the file being downloaded.

        Returns:
            Confirmation of tracking success.

        Raises:
            NotFoundException: If no file with the given ID exists.
        """
        file = await release_file_service.get(file_id)
        if not file:
            raise NotFoundException(f"File with ID {file_id} not found")

        try:
            store = request.app.stores.get("response_cache")
            if store and isinstance(store, RedisStore):
                redis = store._redis
                stats_service = DownloadStatsService(redis)
                await stats_service.track_download(
                    file_id=str(file_id),
                    release_id=str(file.release_id) if file.release_id else None,
                )
                return {"success": True, "file_id": str(file_id)}
        except Exception as e:
            logger.exception(f"Failed to track download for file {file_id}")
            return {"success": False, "error": str(e)}

        return {"success": False, "error": "Redis not available"}


class DownloadsPageController(Controller):
    """Controller for download HTML pages."""

    path = "/downloads"
    include_in_schema = False

    @get("/")
    async def downloads_index(self, release_service: ReleaseService) -> Template:
        """Render the main downloads page."""
        latest_python3 = await release_service.get_latest(PythonVersion.PYTHON3)
        latest_python2 = await release_service.get_latest(PythonVersion.PYTHON2)
        grouped_releases = await release_service.get_releases_grouped_by_minor_version()

        return Template(
            template_name="downloads/index.html.jinja2",
            context={
                "latest_python3": latest_python3,
                "latest_python2": latest_python2,
                "grouped_releases": grouped_releases,
            },
        )

    @get("/release/{slug:str}/")
    async def release_detail(self, slug: str, release_service: ReleaseService) -> Template:
        """Render the release detail page."""
        release = await release_service.get_by_slug(slug)
        if not release:
            raise NotFoundException(f"Release {slug} not found")

        files_by_os = await release_service.get_files_grouped_by_os(release.id)

        return Template(
            template_name="downloads/release.html.jinja2",
            context={
                "release": release,
                "files_by_os": files_by_os,
            },
        )

    @get("/source/")
    async def source_downloads(self, release_service: ReleaseService) -> Template:
        """Render the source downloads page."""
        releases = await release_service.get_for_download_page()

        return Template(
            template_name="downloads/source.html.jinja2",
            context={
                "releases": releases,
            },
        )

    @get("/windows/")
    async def windows_downloads(
        self,
        release_service: ReleaseService,
        os_service: OSService,
    ) -> Template:
        """Render the Windows downloads page."""
        latest_release = await release_service.get_latest(PythonVersion.PYTHON3)
        windows_os = await os_service.get_by_slug("windows")

        return Template(
            template_name="downloads/windows.html.jinja2",
            context={
                "latest_release": latest_release,
                "os": windows_os,
            },
        )

    @get("/macos/")
    async def macos_downloads(
        self,
        release_service: ReleaseService,
        os_service: OSService,
    ) -> Template:
        """Render the macOS downloads page."""
        latest_release = await release_service.get_latest(PythonVersion.PYTHON3)
        macos_os = await os_service.get_by_slug("macos")

        return Template(
            template_name="downloads/macos.html.jinja2",
            context={
                "latest_release": latest_release,
                "os": macos_os,
            },
        )

    @get("/alternatives/")
    async def alternatives_downloads(self) -> Template:
        """Render the alternative Python implementations page."""
        return Template(
            template_name="downloads/alternatives.html.jinja2",
            context={
                "page_title": "Alternative Python Implementations",
            },
        )

    @get("/other/")
    async def other_downloads(self) -> Template:
        """Render the other download resources page."""
        return Template(
            template_name="downloads/other.html.jinja2",
            context={
                "page_title": "Other Download Resources",
            },
        )

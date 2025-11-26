"""Downloads domain API and page controllers."""

from __future__ import annotations

from typing import Annotated

from litestar import Controller, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Parameter
from litestar.response import Template

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

from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from pydotorg.domains.downloads.services import OSService, ReleaseFileService, ReleaseService


class OSController(Controller):
    """Controller for OS CRUD operations."""

    path = "/api/v1/os"
    tags = ["os"]

    @get("/")
    async def list_os(
        self,
        os_service: OSService,
        limit_offset: LimitOffset,
    ) -> list[OSRead]:
        """List all operating systems with pagination."""
        os_list, _total = await os_service.list_and_count(limit_offset)
        return [OSRead.model_validate(os) for os in os_list]

    @get("/{os_id:uuid}")
    async def get_os(
        self,
        os_service: OSService,
        os_id: Annotated[UUID, Parameter(title="OS ID", description="The OS ID")],
    ) -> OSRead:
        """Get an OS by ID."""
        os = await os_service.get(os_id)
        return OSRead.model_validate(os)

    @get("/slug/{slug:str}")
    async def get_os_by_slug(
        self,
        os_service: OSService,
        slug: Annotated[str, Parameter(title="Slug", description="The OS slug")],
    ) -> OSRead:
        """Get an OS by slug."""
        os = await os_service.get_by_slug(slug)
        if not os:
            raise NotFoundException(f"OS with slug {slug} not found")
        return OSRead.model_validate(os)

    @post("/")
    async def create_os(
        self,
        os_service: OSService,
        data: OSCreate,
    ) -> OSRead:
        """Create a new OS."""
        os = await os_service.create(data.model_dump())
        return OSRead.model_validate(os)

    @delete("/{os_id:uuid}")
    async def delete_os(
        self,
        os_service: OSService,
        os_id: Annotated[UUID, Parameter(title="OS ID", description="The OS ID")],
    ) -> None:
        """Delete an OS."""
        await os_service.delete(os_id)


class ReleaseController(Controller):
    """Controller for Release CRUD operations."""

    path = "/api/v1/releases"
    tags = ["releases"]

    @get("/")
    async def list_releases(
        self,
        release_service: ReleaseService,
        limit_offset: LimitOffset,
    ) -> list[ReleaseList]:
        """List all releases with pagination."""
        releases, _total = await release_service.list_and_count(limit_offset)
        return [ReleaseList.model_validate(release) for release in releases]

    @get("/{release_id:uuid}")
    async def get_release(
        self,
        release_service: ReleaseService,
        release_id: Annotated[UUID, Parameter(title="Release ID", description="The release ID")],
    ) -> ReleaseRead:
        """Get a release by ID."""
        release = await release_service.get(release_id)
        return ReleaseRead.model_validate(release)

    @get("/slug/{slug:str}")
    async def get_release_by_slug(
        self,
        release_service: ReleaseService,
        slug: Annotated[str, Parameter(title="Slug", description="The release slug")],
    ) -> ReleaseRead:
        """Get a release by slug."""
        release = await release_service.get_by_slug(slug)
        if not release:
            raise NotFoundException(f"Release with slug {slug} not found")
        return ReleaseRead.model_validate(release)

    @get("/latest")
    async def get_latest_release(
        self,
        release_service: ReleaseService,
    ) -> ReleaseRead:
        """Get the latest Python 3 release."""
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
        """Get the latest release for a specific Python version."""
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
        """List all published releases."""
        releases = await release_service.get_published(limit=limit, offset=offset)
        return [ReleaseList.model_validate(release) for release in releases]

    @get("/download-page")
    async def list_download_page_releases(
        self,
        release_service: ReleaseService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
    ) -> list[ReleaseList]:
        """List releases for the download page."""
        releases = await release_service.get_for_download_page(limit=limit)
        return [ReleaseList.model_validate(release) for release in releases]

    @post("/")
    async def create_release(
        self,
        release_service: ReleaseService,
        data: ReleaseCreate,
    ) -> ReleaseRead:
        """Create a new release."""
        release = await release_service.create(data.model_dump())
        return ReleaseRead.model_validate(release)

    @put("/{release_id:uuid}")
    async def update_release(
        self,
        release_service: ReleaseService,
        data: ReleaseUpdate,
        release_id: Annotated[UUID, Parameter(title="Release ID", description="The release ID")],
    ) -> ReleaseRead:
        """Update a release."""
        update_data = data.model_dump(exclude_unset=True)
        release = await release_service.update(release_id, update_data)
        return ReleaseRead.model_validate(release)

    @delete("/{release_id:uuid}")
    async def delete_release(
        self,
        release_service: ReleaseService,
        release_id: Annotated[UUID, Parameter(title="Release ID", description="The release ID")],
    ) -> None:
        """Delete a release."""
        await release_service.delete(release_id)


class ReleaseFileController(Controller):
    """Controller for ReleaseFile CRUD operations."""

    path = "/api/v1/files"
    tags = ["release-files"]

    @get("/{file_id:uuid}")
    async def get_file(
        self,
        release_file_service: ReleaseFileService,
        file_id: Annotated[UUID, Parameter(title="File ID", description="The file ID")],
    ) -> ReleaseFileRead:
        """Get a release file by ID."""
        file = await release_file_service.get(file_id)
        return ReleaseFileRead.model_validate(file)

    @get("/release/{release_id:uuid}")
    async def list_files_by_release(
        self,
        release_file_service: ReleaseFileService,
        release_id: Annotated[UUID, Parameter(title="Release ID", description="The release ID")],
    ) -> list[ReleaseFileRead]:
        """List all files for a release."""
        files = await release_file_service.get_by_release_id(release_id)
        return [ReleaseFileRead.model_validate(file) for file in files]

    @get("/os/{os_id:uuid}")
    async def list_files_by_os(
        self,
        release_file_service: ReleaseFileService,
        os_id: Annotated[UUID, Parameter(title="OS ID", description="The OS ID")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
    ) -> list[ReleaseFileRead]:
        """List all files for an OS."""
        files = await release_file_service.get_by_os_id(os_id, limit=limit)
        return [ReleaseFileRead.model_validate(file) for file in files]

    @get("/slug/{slug:str}")
    async def get_file_by_slug(
        self,
        release_file_service: ReleaseFileService,
        slug: Annotated[str, Parameter(title="Slug", description="The file slug")],
    ) -> ReleaseFileRead:
        """Get a release file by slug."""
        file = await release_file_service.get_by_slug(slug)
        if not file:
            raise NotFoundException(f"File with slug {slug} not found")
        return ReleaseFileRead.model_validate(file)

    @post("/")
    async def create_file(
        self,
        release_file_service: ReleaseFileService,
        data: ReleaseFileCreate,
    ) -> ReleaseFileRead:
        """Create a new release file."""
        file = await release_file_service.create(data.model_dump())
        return ReleaseFileRead.model_validate(file)

    @delete("/{file_id:uuid}")
    async def delete_file(
        self,
        release_file_service: ReleaseFileService,
        file_id: Annotated[UUID, Parameter(title="File ID", description="The file ID")],
    ) -> None:
        """Delete a release file."""
        await release_file_service.delete(file_id)


class DownloadsPageController(Controller):
    """Controller for download HTML pages."""

    path = "/downloads"

    @get("/")
    async def downloads_index(self, release_service: ReleaseService) -> Template:
        """Render the main downloads page."""
        latest_python3 = await release_service.get_latest(PythonVersion.PYTHON3)
        latest_python2 = await release_service.get_latest(PythonVersion.PYTHON2)
        releases = await release_service.get_for_download_page()

        return Template(
            template_name="downloads/index.html.jinja2",
            context={
                "latest_python3": latest_python3,
                "latest_python2": latest_python2,
                "releases": releases,
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

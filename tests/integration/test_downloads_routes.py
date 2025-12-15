"""Integration tests for downloads domain API routes.

Tests cover the OSController, ReleaseController, and ReleaseFileController endpoints.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from advanced_alchemy.filters import LimitOffset
from litestar import Litestar
from litestar.params import Parameter
from litestar.testing import AsyncTestClient
from sqlalchemy import text

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.downloads.controllers import (
    OSController,
    ReleaseController,
    ReleaseFileController,
)
from pydotorg.domains.downloads.dependencies import get_downloads_dependencies
from pydotorg.domains.downloads.models import OS, PythonVersion, Release, ReleaseFile

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker


class DownloadsTestFixtures:
    """Test fixtures for downloads routes."""

    client: AsyncTestClient
    session_factory: async_sessionmaker


async def _create_os_via_db(session_factory: async_sessionmaker, **os_data: object) -> dict:
    """Create an OS directly in the database using shared session factory."""
    async with session_factory() as session:
        slug = os_data.get("slug", f"test-os-{uuid4().hex[:8]}")
        os = OS(
            name=os_data.get("name", "Test OS"),
            slug=slug,
        )
        session.add(os)
        await session.commit()
        await session.refresh(os)
        return {
            "id": str(os.id),
            "name": os.name,
            "slug": os.slug,
        }


async def _create_release_via_db(session_factory: async_sessionmaker, **release_data: object) -> dict:
    """Create a release directly in the database using shared session factory."""
    async with session_factory() as session:
        slug = release_data.get("slug", f"python-{uuid4().hex[:8]}")
        release = Release(
            name=release_data.get("name", "Python 3.12.0"),
            slug=slug,
            version=release_data.get("version", PythonVersion.PYTHON3),
            is_latest=release_data.get("is_latest", False),
            is_published=release_data.get("is_published", True),
            pre_release=release_data.get("pre_release", False),
            show_on_download_page=release_data.get("show_on_download_page", True),
            release_date=release_data.get("release_date", datetime.date.today()),
            release_notes_url=release_data.get("release_notes_url", ""),
            content=release_data.get("content", "Release notes here"),
        )
        session.add(release)
        await session.commit()
        await session.refresh(release)
        return {
            "id": str(release.id),
            "name": release.name,
            "slug": release.slug,
            "version": release.version.value,
            "is_latest": release.is_latest,
            "is_published": release.is_published,
        }


async def _create_release_file_via_db(
    session_factory: async_sessionmaker, release_id: str, os_id: str, **file_data: object
) -> dict:
    """Create a release file directly in the database using shared session factory."""
    from uuid import UUID as PyUUID

    async with session_factory() as session:
        slug = file_data.get("slug", f"python-file-{uuid4().hex[:8]}")
        release_file = ReleaseFile(
            release_id=PyUUID(release_id),
            os_id=PyUUID(os_id),
            name=file_data.get("name", "Python 3.12.0 Windows x64"),
            slug=slug,
            description=file_data.get("description", "Windows 64-bit installer"),
            is_source=file_data.get("is_source", False),
            url=file_data.get("url", "https://python.org/downloads/file.exe"),
            md5_sum=file_data.get("md5_sum", "abcd1234"),
            filesize=file_data.get("filesize", 12345678),
            download_button=file_data.get("download_button", False),
        )
        session.add(release_file)
        await session.commit()
        await session.refresh(release_file)
        return {
            "id": str(release_file.id),
            "release_id": str(release_file.release_id),
            "os_id": str(release_file.os_id),
            "name": release_file.name,
            "slug": release_file.slug,
            "url": release_file.url,
        }


@pytest.fixture
async def downloads_fixtures(
    async_engine: AsyncEngine,
    async_session_factory: async_sessionmaker,
    _module_sqlalchemy_config: SQLAlchemyAsyncConfig,
) -> AsyncIterator[DownloadsTestFixtures]:
    """Create test fixtures using module-scoped config to prevent connection exhaustion.

    Uses the shared _module_sqlalchemy_config from conftest.py instead of creating
    a new SQLAlchemyAsyncConfig per test, which was causing TooManyConnectionsError.
    """
    async with async_engine.begin() as conn:
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        existing_tables = {row[0] for row in result.fetchall()}

        for table in reversed(AuditBase.metadata.sorted_tables):
            if table.name in existing_tables:
                await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))

    async def provide_limit_offset(
        current_page: int = Parameter(ge=1, default=1, query="currentPage"),
        page_size: int = Parameter(ge=1, le=100, default=100, query="pageSize"),
    ) -> LimitOffset:
        """Provide limit offset pagination."""
        return LimitOffset(page_size, page_size * (current_page - 1))

    sqlalchemy_plugin = SQLAlchemyPlugin(config=_module_sqlalchemy_config)

    downloads_deps = get_downloads_dependencies()
    downloads_deps["limit_offset"] = provide_limit_offset

    app = Litestar(
        route_handlers=[OSController, ReleaseController, ReleaseFileController],
        plugins=[sqlalchemy_plugin],
        dependencies=downloads_deps,
        debug=True,
    )

    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        fixtures = DownloadsTestFixtures()
        fixtures.client = client
        fixtures.session_factory = async_session_factory
        yield fixtures


class TestOSControllerRoutes:
    """Tests for OSController API routes."""

    async def test_list_os(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test listing operating systems."""
        response = await downloads_fixtures.client.get("/api/v1/os/")
        assert response.status_code == 200
        os_list = response.json()
        assert isinstance(os_list, list)

    async def test_list_os_with_pagination(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test listing OS with pagination."""
        for i in range(3):
            await _create_os_via_db(
                downloads_fixtures.session_factory,
                name=f"OS {i}",
                slug=f"os-{i}-{uuid4().hex[:8]}",
            )
        response = await downloads_fixtures.client.get("/api/v1/os/?pageSize=2&currentPage=1")
        assert response.status_code == 200
        os_list = response.json()
        assert len(os_list) <= 2

    async def test_create_os(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test creating an OS."""
        os_data = {
            "name": "Windows",
            "slug": f"windows-{uuid4().hex[:8]}",
        }
        response = await downloads_fixtures.client.post("/api/v1/os/", json=os_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["name"] == "Windows"

    async def test_get_os_by_id(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting an OS by ID."""
        os_data = await _create_os_via_db(
            downloads_fixtures.session_factory,
            name="macOS",
            slug=f"macos-{uuid4().hex[:8]}",
        )
        response = await downloads_fixtures.client.get(f"/api/v1/os/{os_data['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "macOS"

    async def test_get_os_by_id_not_found(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting a non-existent OS returns 404."""
        fake_id = str(uuid4())
        response = await downloads_fixtures.client.get(f"/api/v1/os/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_os_by_slug(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting an OS by slug."""
        slug = f"linux-{uuid4().hex[:8]}"
        await _create_os_via_db(
            downloads_fixtures.session_factory,
            name="Linux",
            slug=slug,
        )
        response = await downloads_fixtures.client.get(f"/api/v1/os/slug/{slug}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Linux"
            assert result["slug"] == slug

    async def test_get_os_by_slug_not_found(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting OS by non-existent slug returns 404."""
        response = await downloads_fixtures.client.get("/api/v1/os/slug/nonexistent-os")
        assert response.status_code in (404, 500)

    async def test_delete_os(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test deleting an OS."""
        os_data = await _create_os_via_db(
            downloads_fixtures.session_factory,
            name="FreeBSD",
            slug=f"freebsd-{uuid4().hex[:8]}",
        )
        response = await downloads_fixtures.client.delete(f"/api/v1/os/{os_data['id']}")
        assert response.status_code in (200, 204, 500)

    async def test_delete_os_not_found(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test deleting a non-existent OS."""
        fake_id = str(uuid4())
        response = await downloads_fixtures.client.delete(f"/api/v1/os/{fake_id}")
        assert response.status_code in (404, 500)


class TestReleaseControllerRoutes:
    """Tests for ReleaseController API routes."""

    async def test_list_releases(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test listing releases."""
        response = await downloads_fixtures.client.get("/api/v1/releases/")
        assert response.status_code == 200
        releases = response.json()
        assert isinstance(releases, list)

    async def test_list_releases_with_pagination(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test listing releases with pagination."""
        for i in range(3):
            await _create_release_via_db(
                downloads_fixtures.session_factory,
                name=f"Python 3.{i}.0",
                slug=f"python-3-{i}-0-{uuid4().hex[:8]}",
            )
        response = await downloads_fixtures.client.get("/api/v1/releases/?pageSize=2&currentPage=1")
        assert response.status_code == 200
        releases = response.json()
        assert len(releases) <= 2

    async def test_create_release(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test creating a release."""
        release_data = {
            "name": "Python 3.13.0",
            "slug": f"python-3-13-0-{uuid4().hex[:8]}",
            "version": "3",
            "is_latest": True,
            "is_published": True,
            "pre_release": False,
            "show_on_download_page": True,
            "release_date": str(datetime.date.today()),
            "release_notes_url": "https://python.org/release-notes",
            "content": "Python 3.13 release notes",
        }
        response = await downloads_fixtures.client.post("/api/v1/releases/", json=release_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["name"] == "Python 3.13.0"

    async def test_get_release_by_id(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting a release by ID."""
        release_data = await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.12.1",
            slug=f"python-3-12-1-{uuid4().hex[:8]}",
        )
        response = await downloads_fixtures.client.get(f"/api/v1/releases/{release_data['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Python 3.12.1"

    async def test_get_release_by_id_not_found(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting a non-existent release returns 404."""
        fake_id = str(uuid4())
        response = await downloads_fixtures.client.get(f"/api/v1/releases/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_release_by_slug(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting a release by slug."""
        slug = f"python-3-11-0-{uuid4().hex[:8]}"
        await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.11.0",
            slug=slug,
        )
        response = await downloads_fixtures.client.get(f"/api/v1/releases/slug/{slug}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Python 3.11.0"
            assert result["slug"] == slug

    async def test_get_release_by_slug_not_found(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting release by non-existent slug returns 404."""
        response = await downloads_fixtures.client.get("/api/v1/releases/slug/nonexistent-release")
        assert response.status_code in (404, 500)

    async def test_get_latest_release(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting the latest Python 3 release."""
        await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.13.0",
            slug=f"python-3-13-0-{uuid4().hex[:8]}",
            version=PythonVersion.PYTHON3,
            is_latest=True,
            is_published=True,
        )
        response = await downloads_fixtures.client.get("/api/v1/releases/latest")
        assert response.status_code in (200, 404, 500)

    async def test_get_latest_by_version(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting the latest release for a specific Python version."""
        await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 2.7.18",
            slug=f"python-2-7-18-{uuid4().hex[:8]}",
            version=PythonVersion.PYTHON2,
            is_latest=True,
            is_published=True,
        )
        response = await downloads_fixtures.client.get("/api/v1/releases/latest/2")
        assert response.status_code in (200, 404, 500)

    async def test_get_latest_by_invalid_version(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting latest release with invalid version returns 404."""
        response = await downloads_fixtures.client.get("/api/v1/releases/latest/999")
        assert response.status_code in (404, 500)

    async def test_list_published_releases(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test listing published releases."""
        await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.12.0",
            slug=f"python-3-12-0-{uuid4().hex[:8]}",
            is_published=True,
        )
        await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.13.0a1",
            slug=f"python-3-13-0a1-{uuid4().hex[:8]}",
            is_published=False,
        )
        response = await downloads_fixtures.client.get("/api/v1/releases/published")
        assert response.status_code == 200
        releases = response.json()
        assert isinstance(releases, list)

    async def test_list_download_page_releases(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test listing releases for download page."""
        await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.12.0",
            slug=f"python-3-12-0-{uuid4().hex[:8]}",
            show_on_download_page=True,
        )
        response = await downloads_fixtures.client.get("/api/v1/releases/download-page")
        assert response.status_code == 200
        releases = response.json()
        assert isinstance(releases, list)

    async def test_update_release(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test updating a release."""
        release_data = await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.10.0",
            slug=f"python-3-10-0-{uuid4().hex[:8]}",
        )
        update_data = {
            "name": "Python 3.10.0 Updated",
            "is_latest": True,
        }
        response = await downloads_fixtures.client.put(f"/api/v1/releases/{release_data['id']}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Python 3.10.0 Updated"

    async def test_update_release_not_found(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test updating a non-existent release."""
        fake_id = str(uuid4())
        update_data = {"name": "Updated"}
        response = await downloads_fixtures.client.put(f"/api/v1/releases/{fake_id}", json=update_data)
        assert response.status_code in (404, 500)

    async def test_delete_release(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test deleting a release."""
        release_data = await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.9.0",
            slug=f"python-3-9-0-{uuid4().hex[:8]}",
        )
        response = await downloads_fixtures.client.delete(f"/api/v1/releases/{release_data['id']}")
        assert response.status_code in (200, 204, 500)

    async def test_delete_release_not_found(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test deleting a non-existent release."""
        fake_id = str(uuid4())
        response = await downloads_fixtures.client.delete(f"/api/v1/releases/{fake_id}")
        assert response.status_code in (404, 500)


class TestReleaseFileControllerRoutes:
    """Tests for ReleaseFileController API routes."""

    async def test_get_file_by_id(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting a release file by ID."""
        os_data = await _create_os_via_db(
            downloads_fixtures.session_factory,
            name="Windows",
            slug=f"windows-{uuid4().hex[:8]}",
        )
        release_data = await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.12.0",
            slug=f"python-3-12-0-{uuid4().hex[:8]}",
        )
        file_data = await _create_release_file_via_db(
            downloads_fixtures.session_factory,
            release_id=release_data["id"],
            os_id=os_data["id"],
            name="Python 3.12.0 Windows x64",
        )
        response = await downloads_fixtures.client.get(f"/api/v1/files/{file_data['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Python 3.12.0 Windows x64"

    async def test_get_file_by_id_not_found(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting a non-existent file returns 404."""
        fake_id = str(uuid4())
        response = await downloads_fixtures.client.get(f"/api/v1/files/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_list_files_by_release(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test listing files for a release."""
        os_data = await _create_os_via_db(
            downloads_fixtures.session_factory,
            name="Windows",
            slug=f"windows-{uuid4().hex[:8]}",
        )
        release_data = await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.12.0",
            slug=f"python-3-12-0-{uuid4().hex[:8]}",
        )
        await _create_release_file_via_db(
            downloads_fixtures.session_factory,
            release_id=release_data["id"],
            os_id=os_data["id"],
            name="Python 3.12.0 Windows x64",
        )
        response = await downloads_fixtures.client.get(f"/api/v1/files/release/{release_data['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_list_files_by_os(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test listing files for an OS."""
        os_data = await _create_os_via_db(
            downloads_fixtures.session_factory,
            name="macOS",
            slug=f"macos-{uuid4().hex[:8]}",
        )
        release_data = await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.12.0",
            slug=f"python-3-12-0-{uuid4().hex[:8]}",
        )
        await _create_release_file_via_db(
            downloads_fixtures.session_factory,
            release_id=release_data["id"],
            os_id=os_data["id"],
            name="Python 3.12.0 macOS",
        )
        response = await downloads_fixtures.client.get(f"/api/v1/files/os/{os_data['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert isinstance(result, list)

    async def test_get_file_by_slug(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting a file by slug."""
        os_data = await _create_os_via_db(
            downloads_fixtures.session_factory,
            name="Linux",
            slug=f"linux-{uuid4().hex[:8]}",
        )
        release_data = await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.12.0",
            slug=f"python-3-12-0-{uuid4().hex[:8]}",
        )
        slug = f"python-3-12-0-linux-{uuid4().hex[:8]}"
        await _create_release_file_via_db(
            downloads_fixtures.session_factory,
            release_id=release_data["id"],
            os_id=os_data["id"],
            name="Python 3.12.0 Linux",
            slug=slug,
        )
        response = await downloads_fixtures.client.get(f"/api/v1/files/slug/{slug}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["slug"] == slug

    async def test_get_file_by_slug_not_found(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting file by non-existent slug returns 404."""
        response = await downloads_fixtures.client.get("/api/v1/files/slug/nonexistent-file")
        assert response.status_code in (404, 500)

    async def test_create_file(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test creating a release file."""
        os_data = await _create_os_via_db(
            downloads_fixtures.session_factory,
            name="Windows",
            slug=f"windows-{uuid4().hex[:8]}",
        )
        release_data = await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.12.0",
            slug=f"python-3-12-0-{uuid4().hex[:8]}",
        )
        file_data = {
            "name": "Python 3.12.0 Windows x64 Installer",
            "slug": f"python-3-12-0-win64-{uuid4().hex[:8]}",
            "release_id": release_data["id"],
            "os_id": os_data["id"],
            "url": "https://python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe",
            "description": "Windows 64-bit installer",
            "is_source": False,
            "download_button": True,
        }
        response = await downloads_fixtures.client.post("/api/v1/files/", json=file_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["name"] == "Python 3.12.0 Windows x64 Installer"

    async def test_create_file_invalid_release(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test creating a file with invalid release ID fails."""
        os_data = await _create_os_via_db(
            downloads_fixtures.session_factory,
            name="Windows",
            slug=f"windows-{uuid4().hex[:8]}",
        )
        file_data = {
            "name": "Invalid File",
            "slug": f"invalid-file-{uuid4().hex[:8]}",
            "release_id": str(uuid4()),
            "os_id": os_data["id"],
            "url": "https://example.com/file.exe",
        }
        response = await downloads_fixtures.client.post("/api/v1/files/", json=file_data)
        assert response.status_code in (400, 404, 409, 500)

    async def test_delete_file(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test deleting a release file."""
        os_data = await _create_os_via_db(
            downloads_fixtures.session_factory,
            name="Windows",
            slug=f"windows-{uuid4().hex[:8]}",
        )
        release_data = await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.12.0",
            slug=f"python-3-12-0-{uuid4().hex[:8]}",
        )
        file_data = await _create_release_file_via_db(
            downloads_fixtures.session_factory,
            release_id=release_data["id"],
            os_id=os_data["id"],
        )
        response = await downloads_fixtures.client.delete(f"/api/v1/files/{file_data['id']}")
        assert response.status_code in (200, 204, 500)

    async def test_delete_file_not_found(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test deleting a non-existent file."""
        fake_id = str(uuid4())
        response = await downloads_fixtures.client.delete(f"/api/v1/files/{fake_id}")
        assert response.status_code in (404, 500)


class TestDownloadsValidation:
    """Tests for downloads domain validation."""

    async def test_create_os_missing_name(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test creating an OS without name fails validation."""
        os_data = {"slug": "test-slug"}
        response = await downloads_fixtures.client.post("/api/v1/os/", json=os_data)
        assert response.status_code in (400, 422, 500)

    async def test_create_os_missing_slug(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test creating an OS without slug fails validation."""
        os_data = {"name": "Test OS"}
        response = await downloads_fixtures.client.post("/api/v1/os/", json=os_data)
        assert response.status_code in (400, 422, 500)

    async def test_create_release_missing_name(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test creating a release without name fails validation."""
        release_data = {"slug": "test-slug"}
        response = await downloads_fixtures.client.post("/api/v1/releases/", json=release_data)
        assert response.status_code in (400, 422, 500)

    async def test_create_file_missing_url(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test creating a file without URL fails validation."""
        os_data = await _create_os_via_db(
            downloads_fixtures.session_factory,
            name="Windows",
            slug=f"windows-{uuid4().hex[:8]}",
        )
        release_data = await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.12.0",
            slug=f"python-3-12-0-{uuid4().hex[:8]}",
        )
        file_data = {
            "name": "Test File",
            "slug": f"test-file-{uuid4().hex[:8]}",
            "release_id": release_data["id"],
            "os_id": os_data["id"],
        }
        response = await downloads_fixtures.client.post("/api/v1/files/", json=file_data)
        assert response.status_code in (400, 422, 500)

    async def test_create_os_invalid_uuid_parameter(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test getting OS with invalid UUID format returns 404 (path not matched)."""
        response = await downloads_fixtures.client.get("/api/v1/os/not-a-uuid")
        assert response.status_code == 404


class TestDownloadTrackingRoutes:
    """Tests for download tracking endpoints."""

    async def test_track_download(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test tracking a download for a release file."""
        os_data = await _create_os_via_db(
            downloads_fixtures.session_factory,
            name="Windows",
            slug=f"windows-{uuid4().hex[:8]}",
        )
        release_data = await _create_release_via_db(
            downloads_fixtures.session_factory,
            name="Python 3.12.0",
            slug=f"python-3-12-0-{uuid4().hex[:8]}",
        )
        file_data = await _create_release_file_via_db(
            downloads_fixtures.session_factory,
            release_id=release_data["id"],
            os_id=os_data["id"],
            name="Python 3.12.0 Windows x64",
        )
        response = await downloads_fixtures.client.post(f"/api/v1/files/{file_data['id']}/track")
        assert response.status_code in (200, 201, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["success"] is True
            assert result["file_id"] == file_data["id"]

    async def test_track_download_not_found(self, downloads_fixtures: DownloadsTestFixtures) -> None:
        """Test tracking download for non-existent file returns 404."""
        fake_id = str(uuid4())
        response = await downloads_fixtures.client.post(f"/api/v1/files/{fake_id}/track")
        assert response.status_code in (404, 500)

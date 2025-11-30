"""Downloads domain Pydantic schemas."""

from __future__ import annotations

import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from pydotorg.domains.downloads.models import PythonVersion


class OSBase(BaseModel):
    """Base OS schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=255)]
    slug: Annotated[str, Field(min_length=1, max_length=255)]


class OSCreate(OSBase):
    """Schema for creating a new OS."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "macOS",
                "slug": "macos",
            }
        }
    )


class OSRead(OSBase):
    """Schema for reading OS data."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "macOS",
                "slug": "macos",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            }
        },
    )

    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ReleaseBase(BaseModel):
    """Base release schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=255)]
    slug: Annotated[str, Field(min_length=1, max_length=255)]
    version: PythonVersion = PythonVersion.PYTHON3
    is_latest: bool = False
    is_published: bool = False
    pre_release: bool = False
    show_on_download_page: bool = True
    release_date: datetime.date | None = None
    release_notes_url: str = ""
    content: str = ""


class ReleaseCreate(ReleaseBase):
    """Schema for creating a new release."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Python 3.13.1",
                "slug": "python-3131",
                "version": "python3",
                "is_latest": True,
                "is_published": True,
                "pre_release": False,
                "show_on_download_page": True,
                "release_date": "2025-01-15",
                "release_notes_url": "https://docs.python.org/release/3.13.1/whatsnew/changelog.html",
                "content": "Python 3.13.1 is the first maintenance release of Python 3.13...",
                "release_page_id": "550e8400-e29b-41d4-a716-446655440100",
            }
        }
    )

    release_page_id: UUID | None = None


class ReleaseUpdate(BaseModel):
    """Schema for updating a release."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_latest": True,
                "is_published": True,
                "content": "Updated release notes for Python 3.13.1...",
            }
        }
    )

    name: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    is_latest: bool | None = None
    is_published: bool | None = None
    pre_release: bool | None = None
    show_on_download_page: bool | None = None
    release_date: datetime.date | None = None
    release_notes_url: str | None = None
    content: str | None = None
    release_page_id: UUID | None = None


class ReleaseRead(ReleaseBase):
    """Schema for reading release data."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440010",
                "name": "Python 3.13.1",
                "slug": "python-3131",
                "version": "python3",
                "is_latest": True,
                "is_published": True,
                "pre_release": False,
                "show_on_download_page": True,
                "release_date": "2025-01-15",
                "release_notes_url": "https://docs.python.org/release/3.13.1/whatsnew/changelog.html",
                "content": "Python 3.13.1 is the first maintenance release...",
                "release_page_id": "550e8400-e29b-41d4-a716-446655440100",
                "created_at": "2025-01-15T00:00:00Z",
                "updated_at": "2025-01-15T00:00:00Z",
            }
        },
    )

    id: UUID
    release_page_id: UUID | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ReleaseList(BaseModel):
    """Schema for release list items."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440010",
                "name": "Python 3.13.1",
                "slug": "python-3131",
                "version": "python3",
                "is_latest": True,
                "is_published": True,
                "pre_release": False,
                "release_date": "2025-01-15",
            }
        },
    )

    id: UUID
    name: str
    slug: str
    version: PythonVersion
    is_latest: bool
    is_published: bool
    pre_release: bool
    release_date: datetime.date | None


class ReleaseFileBase(BaseModel):
    """Base release file schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=255)]
    slug: Annotated[str, Field(min_length=1, max_length=255)]
    description: str = ""
    is_source: bool = False
    url: Annotated[str, Field(min_length=1, max_length=500)]
    gpg_signature_file: str = ""
    sigstore_signature_file: str = ""
    sigstore_cert_file: str = ""
    sigstore_bundle_file: str = ""
    sbom_spdx2_file: str = ""
    md5_sum: str = ""
    filesize: int = 0
    download_button: bool = False


class ReleaseFileCreate(ReleaseFileBase):
    """Schema for creating a new release file."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "python-3.13.1-macos11.pkg",
                "slug": "python-3131-macos11-pkg",
                "description": "macOS 64-bit universal2 installer",
                "is_source": False,
                "url": "https://www.python.org/ftp/python/3.13.1/python-3.13.1-macos11.pkg",
                "md5_sum": "abc123def456...",
                "filesize": 45678901,
                "download_button": True,
                "release_id": "550e8400-e29b-41d4-a716-446655440010",
                "os_id": "550e8400-e29b-41d4-a716-446655440001",
            }
        }
    )

    release_id: UUID
    os_id: UUID


class ReleaseFileRead(ReleaseFileBase):
    """Schema for reading release file data."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440020",
                "name": "python-3.13.1-macos11.pkg",
                "slug": "python-3131-macos11-pkg",
                "description": "macOS 64-bit universal2 installer",
                "is_source": False,
                "url": "https://www.python.org/ftp/python/3.13.1/python-3.13.1-macos11.pkg",
                "gpg_signature_file": "",
                "sigstore_signature_file": "",
                "sigstore_cert_file": "",
                "sigstore_bundle_file": "",
                "sbom_spdx2_file": "",
                "md5_sum": "abc123def456...",
                "filesize": 45678901,
                "download_button": True,
                "release_id": "550e8400-e29b-41d4-a716-446655440010",
                "os_id": "550e8400-e29b-41d4-a716-446655440001",
                "created_at": "2025-01-15T00:00:00Z",
                "updated_at": "2025-01-15T00:00:00Z",
            }
        },
    )

    id: UUID
    release_id: UUID
    os_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ReleaseFileWithOS(ReleaseFileRead):
    """Schema for release file with OS information."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440020",
                "name": "python-3.13.1-macos11.pkg",
                "slug": "python-3131-macos11-pkg",
                "description": "macOS 64-bit universal2 installer",
                "is_source": False,
                "url": "https://www.python.org/ftp/python/3.13.1/python-3.13.1-macos11.pkg",
                "md5_sum": "abc123def456...",
                "filesize": 45678901,
                "download_button": True,
                "release_id": "550e8400-e29b-41d4-a716-446655440010",
                "os_id": "550e8400-e29b-41d4-a716-446655440001",
                "created_at": "2025-01-15T00:00:00Z",
                "updated_at": "2025-01-15T00:00:00Z",
                "os": {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "macOS",
                    "slug": "macos",
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z",
                },
            }
        },
    )

    os: OSRead


class DownloadPageData(BaseModel):
    """Schema for download page template data."""

    latest_python3: ReleaseRead | None
    latest_python2: ReleaseRead | None
    all_releases: list[ReleaseList]


class ReleaseDetailPageData(BaseModel):
    """Schema for release detail page template data."""

    release: ReleaseRead
    files_by_os: dict[str, list[ReleaseFileRead]]

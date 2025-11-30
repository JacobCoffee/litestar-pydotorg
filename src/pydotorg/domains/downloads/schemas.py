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


class OSRead(OSBase):
    """Schema for reading OS data."""

    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


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

    release_page_id: UUID | None = None


class ReleaseUpdate(BaseModel):
    """Schema for updating a release."""

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

    id: UUID
    release_page_id: UUID | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ReleaseList(BaseModel):
    """Schema for release list items."""

    id: UUID
    name: str
    slug: str
    version: PythonVersion
    is_latest: bool
    is_published: bool
    pre_release: bool
    release_date: datetime.date | None

    model_config = ConfigDict(from_attributes=True)


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

    release_id: UUID
    os_id: UUID


class ReleaseFileRead(ReleaseFileBase):
    """Schema for reading release file data."""

    id: UUID
    release_id: UUID
    os_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ReleaseFileWithOS(ReleaseFileRead):
    """Schema for release file with OS information."""

    os: OSRead

    model_config = ConfigDict(from_attributes=True)


class DownloadPageData(BaseModel):
    """Schema for download page template data."""

    latest_python3: ReleaseRead | None
    latest_python2: ReleaseRead | None
    all_releases: list[ReleaseList]


class ReleaseDetailPageData(BaseModel):
    """Schema for release detail page template data."""

    release: ReleaseRead
    files_by_os: dict[str, list[ReleaseFileRead]]

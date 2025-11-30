"""Downloads domain models."""

from __future__ import annotations

import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, Boolean, Date, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydotorg.core.database.base import AuditBase, ContentManageableMixin, NameSlugMixin, UUIDAuditBase

if TYPE_CHECKING:
    from pydotorg.domains.pages.models import Page


class PythonVersion(StrEnum):
    PYTHON1 = "1"
    PYTHON2 = "2"
    PYTHON3 = "3"
    PYMANAGER = "manager"


class OS(AuditBase, ContentManageableMixin, NameSlugMixin):
    __tablename__ = "download_os"

    releases: Mapped[list[ReleaseFile]] = relationship(
        "ReleaseFile",
        back_populates="os",
        lazy="noload",
    )


class Release(AuditBase, ContentManageableMixin, NameSlugMixin):
    __tablename__ = "releases"

    version: Mapped[PythonVersion] = mapped_column(
        Enum(PythonVersion, values_callable=lambda x: [e.value for e in x]),
        default=PythonVersion.PYTHON3,
    )
    is_latest: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    pre_release: Mapped[bool] = mapped_column(Boolean, default=False)
    show_on_download_page: Mapped[bool] = mapped_column(Boolean, default=True)
    release_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    release_page_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("pages.id", ondelete="SET NULL"),
        nullable=True,
    )
    release_notes_url: Mapped[str] = mapped_column(String(500), default="")
    content: Mapped[str] = mapped_column(Text, default="")

    release_page: Mapped[Page | None] = relationship("Page", lazy="selectin")
    files: Mapped[list[ReleaseFile]] = relationship(
        "ReleaseFile",
        back_populates="release",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def is_version_at_least(self, min_version: tuple[int, ...]) -> bool:
        try:
            parts = self.name.split(".")
            version_tuple = tuple(int(p) for p in parts[:2] if p.isdigit())
        except (ValueError, IndexError):
            return False
        else:
            return version_tuple >= min_version

    @property
    def is_version_at_least_3_5(self) -> bool:
        return self.is_version_at_least((3, 5))

    @property
    def is_version_at_least_3_9(self) -> bool:
        return self.is_version_at_least((3, 9))

    @property
    def is_version_at_least_3_14(self) -> bool:
        return self.is_version_at_least((3, 14))

    def files_for_os(self, os_slug: str) -> list[ReleaseFile]:
        return [f for f in self.files if f.os.slug == os_slug]

    def download_file_for_os(self, os_slug: str) -> ReleaseFile | None:
        for f in self.files:
            if f.os.slug == os_slug and f.download_button:
                return f
        return None


class ReleaseFile(AuditBase, ContentManageableMixin, NameSlugMixin):
    __tablename__ = "release_files"
    __table_args__ = (
        UniqueConstraint(
            "release_id",
            "os_id",
            "download_button",
            name="uq_release_os_download_button",
        ),
    )

    release_id: Mapped[UUID] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"))
    os_id: Mapped[UUID] = mapped_column(ForeignKey("download_os.id", ondelete="CASCADE"))
    description: Mapped[str] = mapped_column(Text, default="")
    is_source: Mapped[bool] = mapped_column(Boolean, default=False)
    url: Mapped[str] = mapped_column(String(500))
    gpg_signature_file: Mapped[str] = mapped_column(String(500), default="")
    sigstore_signature_file: Mapped[str] = mapped_column(String(500), default="")
    sigstore_cert_file: Mapped[str] = mapped_column(String(500), default="")
    sigstore_bundle_file: Mapped[str] = mapped_column(String(500), default="")
    sbom_spdx2_file: Mapped[str] = mapped_column(String(500), default="")
    md5_sum: Mapped[str] = mapped_column(String(200), default="")
    filesize: Mapped[int] = mapped_column(BigInteger, default=0)
    download_button: Mapped[bool] = mapped_column(Boolean, default=False)

    release: Mapped[Release] = relationship("Release", back_populates="files")
    os: Mapped[OS] = relationship("OS", back_populates="releases", lazy="selectin")
    statistics: Mapped[list[DownloadStatistic]] = relationship(
        "DownloadStatistic",
        back_populates="release_file",
        cascade="all, delete-orphan",
        lazy="noload",
    )


class DownloadStatistic(UUIDAuditBase):
    """Daily download statistics for release files.

    Stores aggregated download counts per file per day for analytics.
    Redis provides real-time counters; this table provides historical data.
    """

    __tablename__ = "download_statistics"
    __table_args__ = (
        UniqueConstraint(
            "release_file_id",
            "date",
            name="uq_download_stats_file_date",
        ),
        Index("ix_download_stats_date", "date"),
        Index("ix_download_stats_file_id", "release_file_id"),
    )

    release_file_id: Mapped[UUID] = mapped_column(
        ForeignKey("release_files.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0)

    release_file: Mapped[ReleaseFile] = relationship(
        "ReleaseFile",
        back_populates="statistics",
    )

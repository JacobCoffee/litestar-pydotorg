"""Pages domain models."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID  # noqa: TC003 - needed for SQLAlchemy column type

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydotorg.core.database.base import AuditBase, ContentManageableMixin


class ContentType(StrEnum):
    MARKDOWN = "markdown"
    RESTRUCTUREDTEXT = "restructuredtext"
    HTML = "html"


class Page(AuditBase, ContentManageableMixin):
    __tablename__ = "pages"

    title: Mapped[str] = mapped_column(String(500))
    keywords: Mapped[str] = mapped_column(String(1000), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    path: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType),
        default=ContentType.MARKDOWN,
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    template_name: Mapped[str] = mapped_column(String(255), default="pages/default.html")

    images: Mapped[list[Image]] = relationship(
        "Image",
        back_populates="page",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    documents: Mapped[list[DocumentFile]] = relationship(
        "DocumentFile",
        back_populates="page",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Image(AuditBase):
    __tablename__ = "page_images"

    page_id: Mapped[UUID] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"))
    image: Mapped[str] = mapped_column(String(500))

    page: Mapped[Page] = relationship("Page", back_populates="images")


class DocumentFile(AuditBase):
    __tablename__ = "page_documents"

    page_id: Mapped[UUID] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"))
    document: Mapped[str] = mapped_column(String(500))

    page: Mapped[Page] = relationship("Page", back_populates="documents")

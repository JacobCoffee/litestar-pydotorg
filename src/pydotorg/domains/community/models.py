"""Community domain models."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydotorg.core.database.base import AuditBase, Base, SlugMixin
from pydotorg.domains.pages.models import ContentType


class Post(AuditBase, SlugMixin):
    __tablename__ = "community_posts"

    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType),
        default=ContentType.MARKDOWN,
    )
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    photos: Mapped[list[Photo]] = relationship(
        "Photo",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    videos: Mapped[list[Video]] = relationship(
        "Video",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    links: Mapped[list[Link]] = relationship(
        "Link",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Photo(Base):
    __tablename__ = "community_photos"

    post_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("community_posts.id", ondelete="CASCADE"),
        nullable=True,
    )
    image: Mapped[str] = mapped_column(String(500))
    caption: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    post: Mapped[Post | None] = relationship("Post", back_populates="photos")


class Video(Base):
    __tablename__ = "community_videos"

    post_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("community_posts.id", ondelete="CASCADE"),
        nullable=True,
    )
    url: Mapped[str] = mapped_column(String(1000))
    title: Mapped[str] = mapped_column(String(500))
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    post: Mapped[Post | None] = relationship("Post", back_populates="videos")


class Link(Base):
    __tablename__ = "community_links"

    post_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("community_posts.id", ondelete="CASCADE"),
        nullable=True,
    )
    url: Mapped[str] = mapped_column(String(1000))
    title: Mapped[str] = mapped_column(String(500))
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    post: Mapped[Post | None] = relationship("Post", back_populates="links")

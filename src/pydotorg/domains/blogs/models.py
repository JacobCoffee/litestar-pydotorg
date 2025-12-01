"""Blogs domain models."""

from __future__ import annotations

import datetime
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydotorg.core.database.base import AuditBase, Base, NameSlugMixin

feed_aggregate_feeds = Table(
    "feed_aggregate_feeds",
    Base.metadata,
    Column("feed_aggregate_id", ForeignKey("feed_aggregates.id", ondelete="CASCADE"), primary_key=True),
    Column("feed_id", ForeignKey("feeds.id", ondelete="CASCADE"), primary_key=True),
)


class Feed(AuditBase):
    __tablename__ = "feeds"

    name: Mapped[str] = mapped_column(String(255))
    website_url: Mapped[str] = mapped_column(String(500))
    feed_url: Mapped[str] = mapped_column(String(500), unique=True)
    last_fetched: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    entries: Mapped[list[BlogEntry]] = relationship(
        "BlogEntry",
        back_populates="feed",
        cascade="all, delete-orphan",
        lazy="noload",
    )


class BlogEntry(AuditBase):
    __tablename__ = "blog_entries"
    __table_args__ = (UniqueConstraint("guid", name="uq_blog_entry_guid"),)

    feed_id: Mapped[UUID] = mapped_column(ForeignKey("feeds.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1000))
    pub_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), index=True)
    guid: Mapped[str] = mapped_column(String(500))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    feed: Mapped[Feed] = relationship("Feed", back_populates="entries", lazy="selectin")


class FeedAggregate(AuditBase, NameSlugMixin):
    __tablename__ = "feed_aggregates"

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    feeds: Mapped[list[Feed]] = relationship(
        "Feed",
        secondary=feed_aggregate_feeds,
        lazy="selectin",
    )


class RelatedBlog(AuditBase):
    __tablename__ = "related_blogs"

    blog_name: Mapped[str] = mapped_column(String(255))
    blog_website: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

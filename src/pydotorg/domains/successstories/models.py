"""Success Stories domain models."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydotorg.core.database.base import AuditBase, Base, NameSlugMixin, SlugMixin
from pydotorg.domains.pages.models import ContentType


class StoryCategory(Base, NameSlugMixin):
    __tablename__ = "story_categories"

    stories: Mapped[list[Story]] = relationship(
        "Story",
        back_populates="category",
        lazy="selectin",
    )


class Story(AuditBase, SlugMixin):
    __tablename__ = "success_stories"

    name: Mapped[str] = mapped_column(String(500))
    company_name: Mapped[str] = mapped_column(String(255))
    company_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category_id: Mapped[UUID] = mapped_column(ForeignKey("story_categories.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType),
        default=ContentType.MARKDOWN,
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    category: Mapped[StoryCategory] = relationship("StoryCategory", back_populates="stories", lazy="selectin")

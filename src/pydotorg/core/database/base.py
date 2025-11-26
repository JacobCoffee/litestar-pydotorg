"""Base SQLAlchemy models and mixins."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - needed for SQLAlchemy column type
from typing import TYPE_CHECKING, Any
from uuid import UUID  # noqa: TC003 - needed for SQLAlchemy column type

from advanced_alchemy.base import UUIDAuditBase, UUIDBase
from slugify import slugify
from sqlalchemy import DateTime, ForeignKey, String, event, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

if TYPE_CHECKING:
    from pydotorg.domains.users.models import User


class Base(UUIDBase):
    __abstract__ = True


class AuditBase(UUIDAuditBase):
    __abstract__ = True


class SlugMixin:
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)

    @classmethod
    def generate_slug(cls, value: str) -> str:
        return slugify(value, max_length=200)


class NameSlugMixin(SlugMixin):
    name: Mapped[str] = mapped_column(String(200))

    @classmethod
    def auto_generate_slug(cls, target: Any, value: str, _oldvalue: str, _initiator: Any) -> None:
        if value and not target.slug:
            target.slug = cls.generate_slug(value)


def register_name_slug_listener(mapper: Any, _class: type[NameSlugMixin]) -> None:
    if hasattr(_class, "name") and hasattr(_class, "auto_generate_slug"):
        event.listen(_class.name, "set", _class.auto_generate_slug, propagate=True)


class ContentManageableMixin:
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        index=True,
        nullable=False,
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @declared_attr
    def creator_id(self) -> Mapped[UUID | None]:
        return mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    @declared_attr
    def creator(self) -> Mapped[User | None]:
        return relationship(
            "User",
            foreign_keys=[self.creator_id],
            lazy="selectin",
        )

    @declared_attr
    def last_modified_by_id(self) -> Mapped[UUID | None]:
        return mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    @declared_attr
    def last_modified_by(self) -> Mapped[User | None]:
        return relationship(
            "User",
            foreign_keys=[self.last_modified_by_id],
            lazy="selectin",
        )

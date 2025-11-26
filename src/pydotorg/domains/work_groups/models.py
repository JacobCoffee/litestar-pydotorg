"""Work Groups domain models."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from pydotorg.core.database.base import AuditBase, SlugMixin


class WorkGroup(AuditBase, SlugMixin):
    __tablename__ = "work_groups"

    name: Mapped[str] = mapped_column(String(255))
    purpose: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

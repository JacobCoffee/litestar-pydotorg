"""Code Samples domain models."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from pydotorg.core.database.base import AuditBase, SlugMixin


class CodeSample(AuditBase, SlugMixin):
    __tablename__ = "code_samples"

    code: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

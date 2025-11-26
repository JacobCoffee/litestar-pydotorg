"""Minutes domain models."""

from __future__ import annotations

import datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from pydotorg.core.database.base import AuditBase, SlugMixin
from pydotorg.domains.pages.models import ContentType


class Minutes(AuditBase, SlugMixin):
    __tablename__ = "minutes"

    date: Mapped[datetime.date] = mapped_column(Date, index=True)
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType, values_callable=lambda x: [e.value for e in x]),
        default=ContentType.MARKDOWN,
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

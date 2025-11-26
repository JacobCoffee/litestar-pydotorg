"""Banners domain models."""

from __future__ import annotations

import datetime

from sqlalchemy import Boolean, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from pydotorg.core.database.base import AuditBase


class Banner(AuditBase):
    __tablename__ = "banners"

    name: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    message: Mapped[str] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    start_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True, index=True)
    end_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True, index=True)

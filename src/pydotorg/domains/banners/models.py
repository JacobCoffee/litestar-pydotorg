"""Banners domain models."""

from __future__ import annotations

import datetime
from enum import Enum

from sqlalchemy import Boolean, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from pydotorg.core.database.base import AuditBase


class BannerType(str, Enum):
    """Banner display type for styling."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class BannerTarget(str, Enum):
    """Where the banner should be displayed when not sitewide."""

    FRONTEND = "frontend"  # Frontend pages only
    API = "api"  # API routes only


class Banner(AuditBase):
    __tablename__ = "banners"

    name: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    message: Mapped[str] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    link_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    banner_type: Mapped[str] = mapped_column(String(20), default=BannerType.INFO.value, index=True)
    target: Mapped[str] = mapped_column(String(20), default=BannerTarget.FRONTEND.value, index=True)
    paths: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_dismissible: Mapped[bool] = mapped_column(Boolean, default=True)
    is_sitewide: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    start_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True, index=True)
    end_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True, index=True)

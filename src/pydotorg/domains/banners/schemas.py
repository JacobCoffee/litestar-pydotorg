"""Banners domain Pydantic schemas."""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BannerTypeEnum(str, Enum):
    """Banner display type for styling."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class BannerBase(BaseModel):
    """Base Banner schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=255)]
    title: Annotated[str, Field(min_length=1, max_length=500)]
    message: str
    link: str | None = None
    link_text: str | None = None
    banner_type: BannerTypeEnum = BannerTypeEnum.INFO
    is_active: bool = False
    is_dismissible: bool = True
    is_sitewide: bool = True
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None


class BannerCreate(BannerBase):
    """Schema for creating a new Banner."""


class BannerUpdate(BaseModel):
    """Schema for updating a Banner."""

    name: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    title: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    message: str | None = None
    link: str | None = None
    link_text: str | None = None
    banner_type: BannerTypeEnum | None = None
    is_active: bool | None = None
    is_dismissible: bool | None = None
    is_sitewide: bool | None = None
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None


class BannerRead(BannerBase):
    """Schema for reading Banner data."""

    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class BannerList(BaseModel):
    """Schema for Banner list items."""

    id: UUID
    name: str
    title: str
    banner_type: BannerTypeEnum
    is_active: bool
    is_dismissible: bool
    is_sitewide: bool
    start_date: datetime.date | None
    end_date: datetime.date | None

    model_config = ConfigDict(from_attributes=True)


class BannerSitewideRead(BaseModel):
    """Schema for reading sitewide banner data (minimal for frontend)."""

    id: UUID
    title: str
    message: str
    link: str | None = None
    link_text: str | None = None
    banner_type: BannerTypeEnum
    is_dismissible: bool

    model_config = ConfigDict(from_attributes=True)

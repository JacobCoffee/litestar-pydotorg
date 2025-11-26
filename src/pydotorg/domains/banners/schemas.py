"""Banners domain Pydantic schemas."""

from __future__ import annotations

import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BannerBase(BaseModel):
    """Base Banner schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=255)]
    title: Annotated[str, Field(min_length=1, max_length=500)]
    message: str
    link: str | None = None
    is_active: bool = False
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
    is_active: bool | None = None
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
    is_active: bool
    start_date: datetime.date | None
    end_date: datetime.date | None

    model_config = ConfigDict(from_attributes=True)

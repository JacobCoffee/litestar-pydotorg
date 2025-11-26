"""Work Groups domain Pydantic schemas."""

from __future__ import annotations

import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkGroupBase(BaseModel):
    """Base WorkGroup schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=255)]
    purpose: str
    active: bool = True
    url: str | None = None


class WorkGroupCreate(WorkGroupBase):
    """Schema for creating a new WorkGroup."""

    creator_id: UUID


class WorkGroupUpdate(BaseModel):
    """Schema for updating a WorkGroup."""

    name: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    purpose: str | None = None
    active: bool | None = None
    url: str | None = None


class WorkGroupRead(WorkGroupBase):
    """Schema for reading WorkGroup data."""

    id: UUID
    slug: str
    creator_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class WorkGroupList(BaseModel):
    """Schema for WorkGroup list items."""

    id: UUID
    slug: str
    name: str
    active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

"""Code Samples domain Pydantic schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    import datetime
    from uuid import UUID


class CodeSampleBase(BaseModel):
    """Base CodeSample schema with common fields."""

    code: str
    description: str
    is_published: bool = False


class CodeSampleCreate(CodeSampleBase):
    """Schema for creating a new CodeSample."""

    creator_id: UUID


class CodeSampleUpdate(BaseModel):
    """Schema for updating a CodeSample."""

    code: str | None = None
    description: str | None = None
    is_published: bool | None = None


class CodeSampleRead(CodeSampleBase):
    """Schema for reading CodeSample data."""

    id: UUID
    slug: str
    creator_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class CodeSampleList(BaseModel):
    """Schema for CodeSample list items."""

    id: UUID
    slug: str
    description: str
    is_published: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

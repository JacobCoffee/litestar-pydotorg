"""Minutes domain Pydantic schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from pydotorg.domains.pages.models import ContentType

if TYPE_CHECKING:
    import datetime
    from uuid import UUID


class MinutesBase(BaseModel):
    """Base Minutes schema with common fields."""

    date: datetime.date
    content: str
    content_type: ContentType = ContentType.MARKDOWN
    is_published: bool = False


class MinutesCreate(MinutesBase):
    """Schema for creating new Minutes."""

    creator_id: UUID


class MinutesUpdate(BaseModel):
    """Schema for updating Minutes."""

    date: datetime.date | None = None
    content: str | None = None
    content_type: ContentType | None = None
    is_published: bool | None = None


class MinutesRead(MinutesBase):
    """Schema for reading Minutes data."""

    id: UUID
    slug: str
    creator_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class MinutesList(BaseModel):
    """Schema for Minutes list items."""

    id: UUID
    slug: str
    date: datetime.date
    is_published: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

"""Success Stories domain Pydantic schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, Field

from pydotorg.domains.pages.models import ContentType

if TYPE_CHECKING:
    import datetime
    from uuid import UUID


class StoryCategoryBase(BaseModel):
    """Base StoryCategory schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=200)]
    slug: Annotated[str, Field(min_length=1, max_length=200)]


class StoryCategoryCreate(StoryCategoryBase):
    """Schema for creating a new StoryCategory."""


class StoryCategoryUpdate(BaseModel):
    """Schema for updating a StoryCategory."""

    name: Annotated[str, Field(min_length=1, max_length=200)] | None = None


class StoryCategoryRead(StoryCategoryBase):
    """Schema for reading StoryCategory data."""

    id: UUID

    model_config = ConfigDict(from_attributes=True)


class StoryBase(BaseModel):
    """Base Story schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=500)]
    company_name: Annotated[str, Field(min_length=1, max_length=255)]
    company_url: str | None = None
    content: str
    content_type: ContentType = ContentType.MARKDOWN
    is_published: bool = False
    featured: bool = False
    image: str | None = None


class StoryCreate(StoryBase):
    """Schema for creating a new Story."""

    category_id: UUID
    creator_id: UUID


class StoryUpdate(BaseModel):
    """Schema for updating a Story."""

    name: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    company_name: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    company_url: str | None = None
    category_id: UUID | None = None
    content: str | None = None
    content_type: ContentType | None = None
    is_published: bool | None = None
    featured: bool | None = None
    image: str | None = None


class StoryRead(StoryBase):
    """Schema for reading Story data."""

    id: UUID
    slug: str
    category_id: UUID
    creator_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class StoryList(BaseModel):
    """Schema for Story list items."""

    id: UUID
    slug: str
    name: str
    company_name: str
    category_id: UUID
    is_published: bool
    featured: bool
    image: str | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class StoryWithCategory(StoryRead):
    """Schema for Story with Category information."""

    category: StoryCategoryRead

    model_config = ConfigDict(from_attributes=True)

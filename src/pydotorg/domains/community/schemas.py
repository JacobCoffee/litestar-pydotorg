"""Community domain Pydantic schemas."""

from __future__ import annotations

import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from pydotorg.domains.pages.models import ContentType


class PostBase(BaseModel):
    """Base Post schema with common fields."""

    title: Annotated[str, Field(min_length=1, max_length=500)]
    content: str
    content_type: ContentType = ContentType.MARKDOWN
    is_published: bool = False


class PostCreate(PostBase):
    """Schema for creating a new Post."""

    creator_id: UUID


class PostUpdate(BaseModel):
    """Schema for updating a Post."""

    title: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    content: str | None = None
    content_type: ContentType | None = None
    is_published: bool | None = None


class PostRead(PostBase):
    """Schema for reading Post data."""

    id: UUID
    slug: str
    creator_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class PostList(BaseModel):
    """Schema for Post list items."""

    id: UUID
    slug: str
    title: str
    is_published: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class PhotoBase(BaseModel):
    """Base Photo schema with common fields."""

    image: Annotated[str, Field(min_length=1, max_length=500)]
    caption: str | None = None


class PhotoCreate(PhotoBase):
    """Schema for creating a new Photo."""

    post_id: UUID | None = None
    creator_id: UUID


class PhotoUpdate(BaseModel):
    """Schema for updating a Photo."""

    image: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    caption: str | None = None
    post_id: UUID | None = None


class PhotoRead(PhotoBase):
    """Schema for reading Photo data."""

    id: UUID
    post_id: UUID | None
    creator_id: UUID

    model_config = ConfigDict(from_attributes=True)


class VideoBase(BaseModel):
    """Base Video schema with common fields."""

    url: Annotated[str, Field(min_length=1, max_length=1000)]
    title: Annotated[str, Field(min_length=1, max_length=500)]


class VideoCreate(VideoBase):
    """Schema for creating a new Video."""

    post_id: UUID | None = None
    creator_id: UUID


class VideoUpdate(BaseModel):
    """Schema for updating a Video."""

    url: Annotated[str, Field(min_length=1, max_length=1000)] | None = None
    title: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    post_id: UUID | None = None


class VideoRead(VideoBase):
    """Schema for reading Video data."""

    id: UUID
    post_id: UUID | None
    creator_id: UUID

    model_config = ConfigDict(from_attributes=True)


class LinkBase(BaseModel):
    """Base Link schema with common fields."""

    url: Annotated[str, Field(min_length=1, max_length=1000)]
    title: Annotated[str, Field(min_length=1, max_length=500)]


class LinkCreate(LinkBase):
    """Schema for creating a new Link."""

    post_id: UUID | None = None
    creator_id: UUID


class LinkUpdate(BaseModel):
    """Schema for updating a Link."""

    url: Annotated[str, Field(min_length=1, max_length=1000)] | None = None
    title: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    post_id: UUID | None = None


class LinkRead(LinkBase):
    """Schema for reading Link data."""

    id: UUID
    post_id: UUID | None
    creator_id: UUID

    model_config = ConfigDict(from_attributes=True)


class PostWithMedia(PostRead):
    """Schema for Post with related media."""

    photos: list[PhotoRead]
    videos: list[VideoRead]
    links: list[LinkRead]

    model_config = ConfigDict(from_attributes=True)

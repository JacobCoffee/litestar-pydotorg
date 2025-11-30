"""Pages domain Pydantic schemas."""

from __future__ import annotations

import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from pydotorg.domains.pages.models import ContentType


class PageBase(BaseModel):
    """Base page schema with common fields."""

    title: Annotated[str, Field(min_length=1, max_length=500)]
    path: Annotated[str, Field(min_length=1, max_length=500)]
    content: str = ""
    content_type: ContentType = ContentType.MARKDOWN
    keywords: Annotated[str, Field(max_length=1000)] = ""
    description: str = ""
    is_published: bool = True
    template_name: Annotated[str, Field(max_length=255)] = "pages/default.html"


class PageCreate(PageBase):
    """Schema for creating a new page."""

    creator_id: UUID | None = None


class PageUpdate(BaseModel):
    """Schema for updating an existing page."""

    title: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    path: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    content: str | None = None
    content_type: ContentType | None = None
    keywords: Annotated[str, Field(max_length=1000)] | None = None
    description: str | None = None
    is_published: bool | None = None
    template_name: Annotated[str, Field(max_length=255)] | None = None
    last_modified_by_id: UUID | None = None


class PageRead(PageBase):
    """Schema for reading page data."""

    id: UUID
    created: datetime.datetime
    updated: datetime.datetime
    creator_id: UUID | None
    last_modified_by_id: UUID | None

    model_config = ConfigDict(from_attributes=True)


class PagePublic(BaseModel):
    """Public page schema for rendering."""

    id: UUID
    title: str
    path: str
    content: str
    content_type: ContentType
    keywords: str
    description: str
    template_name: str
    created: datetime.datetime
    updated: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ImageBase(BaseModel):
    """Base image schema."""

    image: Annotated[str, Field(max_length=500)]


class ImageCreate(ImageBase):
    """Schema for creating a new image."""

    page_id: UUID
    creator_id: UUID | None = None


class ImageRead(ImageBase):
    """Schema for reading image data."""

    id: UUID
    page_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentFileBase(BaseModel):
    """Base document file schema."""

    document: Annotated[str, Field(max_length=500)]


class DocumentFileCreate(DocumentFileBase):
    """Schema for creating a new document file."""

    page_id: UUID
    creator_id: UUID | None = None


class DocumentFileRead(DocumentFileBase):
    """Schema for reading document file data."""

    id: UUID
    page_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

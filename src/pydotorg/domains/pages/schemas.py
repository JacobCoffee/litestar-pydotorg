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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "About Python",
                "path": "/about/",
                "content": "# About Python\n\nPython is a programming language...",
                "content_type": "markdown",
                "keywords": "python, programming, language",
                "description": "Learn about the Python programming language",
                "is_published": True,
                "template_name": "pages/default.html",
            }
        }
    )

    creator_id: UUID | None = None


class PageUpdate(BaseModel):
    """Schema for updating an existing page."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "# About Python\n\nUpdated content about Python...",
                "is_published": True,
            }
        }
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "title": "About Python",
                "path": "/about/",
                "content": "# About Python\n\nPython is a programming language...",
                "content_type": "markdown",
                "keywords": "python, programming, language",
                "description": "Learn about the Python programming language",
                "is_published": True,
                "template_name": "pages/default.html",
                "created": "2025-01-01T00:00:00Z",
                "updated": "2025-01-15T10:00:00Z",
                "creator_id": "550e8400-e29b-41d4-a716-446655440000",
                "last_modified_by_id": None,
            }
        },
    )

    id: UUID
    created: datetime.datetime
    updated: datetime.datetime
    creator_id: UUID | None
    last_modified_by_id: UUID | None


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

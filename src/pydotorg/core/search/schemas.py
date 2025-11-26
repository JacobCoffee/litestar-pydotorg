"""Search schemas for Meilisearch integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class SearchQuery(BaseModel):
    """Search query parameters."""

    query: str = Field(..., min_length=1, description="Search query string")
    indexes: list[str] | None = Field(default=None, description="Specific indexes to search in")
    filters: dict[str, Any] | None = Field(default=None, description="Additional search filters")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results per index")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    attributes_to_retrieve: list[str] | None = Field(default=None, description="Specific attributes to return")
    attributes_to_highlight: list[str] | None = Field(default=None, description="Attributes to highlight in results")


class SearchHit(BaseModel):
    """A single search result hit."""

    id: str = Field(..., description="Document ID")
    index: str = Field(..., description="Index the document came from")
    title: str = Field(..., description="Document title")
    description: str | None = Field(default=None, description="Document description")
    url: str = Field(..., description="Document URL")
    content_type: str = Field(..., description="Type of content (job, event, blog, page)")
    created: datetime | None = Field(default=None, description="Creation timestamp")
    modified: datetime | None = Field(default=None, description="Last modification timestamp")
    highlight: dict[str, list[str]] | None = Field(default=None, description="Highlighted text snippets")
    extra: dict[str, Any] | None = Field(default=None, description="Additional metadata")


class SearchResult(BaseModel):
    """Search results response."""

    hits: list[SearchHit] = Field(default_factory=list, description="List of search results")
    total: int = Field(..., description="Total number of results found")
    offset: int = Field(default=0, description="Current offset")
    limit: int = Field(default=20, description="Maximum results returned")
    processing_time_ms: int = Field(..., description="Search processing time in milliseconds")
    query: str = Field(..., description="The search query that was executed")


class IndexedDocument(BaseModel):
    """Base schema for indexed documents in Meilisearch."""

    id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    description: str | None = Field(default=None, description="Document description")
    content: str | None = Field(default=None, description="Full searchable content")
    url: str = Field(..., description="Document URL")
    content_type: str = Field(..., description="Type of content (job, event, blog, page)")
    created: datetime | None = Field(default=None, description="Creation timestamp")
    modified: datetime | None = Field(default=None, description="Last modification timestamp")
    status: str | None = Field(default=None, description="Publication status")
    tags: list[str] = Field(default_factory=list, description="Associated tags")
    searchable_text: str | None = Field(default=None, description="Combined searchable text")


class JobDocument(IndexedDocument):
    """Job posting document for search indexing."""

    content_type: str = Field(default="job", frozen=True)
    company_name: str = Field(..., description="Company name")
    location: str | None = Field(default=None, description="Job location")
    remote: bool = Field(default=False, description="Remote position flag")
    job_types: list[str] = Field(default_factory=list, description="Job type categories")


class EventDocument(IndexedDocument):
    """Event document for search indexing."""

    content_type: str = Field(default="event", frozen=True)
    venue: str | None = Field(default=None, description="Event venue")
    location: str | None = Field(default=None, description="Event location")
    start_date: datetime | None = Field(default=None, description="Event start date")
    end_date: datetime | None = Field(default=None, description="Event end date")


class BlogDocument(IndexedDocument):
    """Blog entry document for search indexing."""

    content_type: str = Field(default="blog", frozen=True)
    author: str | None = Field(default=None, description="Blog post author")
    published: datetime | None = Field(default=None, description="Publication date")


class PageDocument(IndexedDocument):
    """CMS page document for search indexing."""

    content_type: str = Field(default="page", frozen=True)
    path: str = Field(..., description="Page path")

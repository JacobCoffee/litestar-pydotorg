"""Blogs domain Pydantic schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    import datetime
    from uuid import UUID


class FeedBase(BaseModel):
    """Base Feed schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=255)]
    website_url: Annotated[str, Field(min_length=1, max_length=500)]
    feed_url: Annotated[str, Field(min_length=1, max_length=500)]
    is_active: bool = True


class FeedCreate(FeedBase):
    """Schema for creating a new Feed."""


class FeedUpdate(BaseModel):
    """Schema for updating a Feed."""

    name: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    website_url: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    feed_url: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    is_active: bool | None = None


class FeedRead(FeedBase):
    """Schema for reading Feed data."""

    id: UUID
    last_fetched: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class FeedList(BaseModel):
    """Schema for Feed list items."""

    id: UUID
    name: str
    website_url: str
    is_active: bool
    last_fetched: datetime.datetime | None

    model_config = ConfigDict(from_attributes=True)


class BlogEntryBase(BaseModel):
    """Base BlogEntry schema with common fields."""

    title: Annotated[str, Field(min_length=1, max_length=500)]
    summary: str | None = None
    content: str | None = None
    url: Annotated[str, Field(min_length=1, max_length=1000)]
    pub_date: datetime.datetime
    guid: Annotated[str, Field(min_length=1, max_length=500)]


class BlogEntryCreate(BlogEntryBase):
    """Schema for creating a new BlogEntry."""

    feed_id: UUID


class BlogEntryUpdate(BaseModel):
    """Schema for updating a BlogEntry."""

    title: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    summary: str | None = None
    content: str | None = None
    url: Annotated[str, Field(min_length=1, max_length=1000)] | None = None
    pub_date: datetime.datetime | None = None


class BlogEntryRead(BlogEntryBase):
    """Schema for reading BlogEntry data."""

    id: UUID
    feed_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class BlogEntryList(BaseModel):
    """Schema for BlogEntry list items."""

    id: UUID
    feed_id: UUID
    title: str
    summary: str | None
    url: str
    pub_date: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class BlogEntryWithFeed(BlogEntryRead):
    """Schema for BlogEntry with Feed information."""

    feed: FeedRead

    model_config = ConfigDict(from_attributes=True)


class FeedAggregateBase(BaseModel):
    """Base FeedAggregate schema with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=255)]
    slug: Annotated[str, Field(min_length=1, max_length=255)]
    description: str | None = None


class FeedAggregateCreate(FeedAggregateBase):
    """Schema for creating a new FeedAggregate."""

    feed_ids: list[UUID] = []


class FeedAggregateUpdate(BaseModel):
    """Schema for updating a FeedAggregate."""

    name: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    description: str | None = None
    feed_ids: list[UUID] | None = None


class FeedAggregateRead(FeedAggregateBase):
    """Schema for reading FeedAggregate data."""

    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class FeedAggregateWithFeeds(FeedAggregateRead):
    """Schema for FeedAggregate with Feeds."""

    feeds: list[FeedRead]

    model_config = ConfigDict(from_attributes=True)


class RelatedBlogBase(BaseModel):
    """Base RelatedBlog schema with common fields."""

    blog_name: Annotated[str, Field(min_length=1, max_length=255)]
    blog_website: Annotated[str, Field(min_length=1, max_length=500)]
    description: str | None = None


class RelatedBlogCreate(RelatedBlogBase):
    """Schema for creating a new RelatedBlog."""


class RelatedBlogUpdate(BaseModel):
    """Schema for updating a RelatedBlog."""

    blog_name: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    blog_website: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    description: str | None = None


class RelatedBlogRead(RelatedBlogBase):
    """Schema for reading RelatedBlog data."""

    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class BlogsPageData(BaseModel):
    """Schema for blogs page template data."""

    recent_entries: list[BlogEntryWithFeed]
    feeds: list[FeedRead]
    related_blogs: list[RelatedBlogRead]


class FeedDetailPageData(BaseModel):
    """Schema for feed detail page template data."""

    feed: FeedRead
    entries: list[BlogEntryList]

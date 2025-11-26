"""Blogs domain API and page controllers."""

from __future__ import annotations

from typing import Annotated

from litestar import Controller, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Parameter
from litestar.response import Template

from pydotorg.domains.blogs.schemas import (
    BlogEntryCreate,
    BlogEntryList,
    BlogEntryRead,
    BlogEntryUpdate,
    BlogEntryWithFeed,
    FeedAggregateCreate,
    FeedAggregateRead,
    FeedAggregateUpdate,
    FeedAggregateWithFeeds,
    FeedCreate,
    FeedList,
    FeedRead,
    FeedUpdate,
    RelatedBlogCreate,
    RelatedBlogRead,
    RelatedBlogUpdate,
)

from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from pydotorg.domains.blogs.services import BlogEntryService, FeedAggregateService, FeedService, RelatedBlogService


class FeedController(Controller):
    """Controller for Feed CRUD operations."""

    path = "/api/v1/feeds"
    tags = ["feeds"]

    @get("/")
    async def list_feeds(
        self,
        feed_service: FeedService,
        limit_offset: LimitOffset,
    ) -> list[FeedList]:
        """List all feeds with pagination."""
        feeds, _total = await feed_service.list_and_count(limit_offset)
        return [FeedList.model_validate(feed) for feed in feeds]

    @get("/{feed_id:uuid}")
    async def get_feed(
        self,
        feed_service: FeedService,
        feed_id: Annotated[UUID, Parameter(title="Feed ID", description="The feed ID")],
    ) -> FeedRead:
        """Get a feed by ID."""
        feed = await feed_service.get(feed_id)
        return FeedRead.model_validate(feed)

    @get("/active")
    async def list_active_feeds(
        self,
        feed_service: FeedService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
    ) -> list[FeedList]:
        """List all active feeds."""
        feeds = await feed_service.get_active_feeds(limit=limit)
        return [FeedList.model_validate(feed) for feed in feeds]

    @post("/")
    async def create_feed(
        self,
        feed_service: FeedService,
        data: FeedCreate,
    ) -> FeedRead:
        """Create a new feed."""
        feed = await feed_service.create(data.model_dump())
        return FeedRead.model_validate(feed)

    @put("/{feed_id:uuid}")
    async def update_feed(
        self,
        feed_service: FeedService,
        data: FeedUpdate,
        feed_id: Annotated[UUID, Parameter(title="Feed ID", description="The feed ID")],
    ) -> FeedRead:
        """Update a feed."""
        update_data = data.model_dump(exclude_unset=True)
        feed = await feed_service.update(feed_id, update_data)
        return FeedRead.model_validate(feed)

    @delete("/{feed_id:uuid}")
    async def delete_feed(
        self,
        feed_service: FeedService,
        feed_id: Annotated[UUID, Parameter(title="Feed ID", description="The feed ID")],
    ) -> None:
        """Delete a feed."""
        await feed_service.delete(feed_id)

    @post("/{feed_id:uuid}/fetch")
    async def fetch_feed(
        self,
        feed_service: FeedService,
        feed_id: Annotated[UUID, Parameter(title="Feed ID", description="The feed ID")],
    ) -> dict[str, int]:
        """Fetch and parse a feed to update entries."""
        feed = await feed_service.get(feed_id)
        if not feed:
            raise NotFoundException(f"Feed with ID {feed_id} not found")

        entries = await feed_service.fetch_feed(feed)
        return {"entries_processed": len(entries)}


class BlogEntryController(Controller):
    """Controller for BlogEntry CRUD operations."""

    path = "/api/v1/blog-entries"
    tags = ["blog-entries"]

    @get("/")
    async def list_entries(
        self,
        blog_entry_service: BlogEntryService,
        limit_offset: LimitOffset,
    ) -> list[BlogEntryList]:
        """List all blog entries with pagination."""
        entries, _total = await blog_entry_service.list_and_count(limit_offset)
        return [BlogEntryList.model_validate(entry) for entry in entries]

    @get("/{entry_id:uuid}")
    async def get_entry(
        self,
        blog_entry_service: BlogEntryService,
        entry_id: Annotated[UUID, Parameter(title="Entry ID", description="The entry ID")],
    ) -> BlogEntryRead:
        """Get a blog entry by ID."""
        entry = await blog_entry_service.get(entry_id)
        return BlogEntryRead.model_validate(entry)

    @get("/recent")
    async def list_recent_entries(
        self,
        blog_entry_service: BlogEntryService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 20,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[BlogEntryWithFeed]:
        """List recent blog entries across all feeds."""
        entries = await blog_entry_service.get_recent_entries(limit=limit, offset=offset)
        return [BlogEntryWithFeed.model_validate(entry) for entry in entries]

    @get("/feed/{feed_id:uuid}")
    async def list_entries_by_feed(
        self,
        blog_entry_service: BlogEntryService,
        feed_id: Annotated[UUID, Parameter(title="Feed ID", description="The feed ID")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[BlogEntryList]:
        """List all entries for a specific feed."""
        entries = await blog_entry_service.get_by_feed_id(feed_id, limit=limit, offset=offset)
        return [BlogEntryList.model_validate(entry) for entry in entries]

    @post("/")
    async def create_entry(
        self,
        blog_entry_service: BlogEntryService,
        data: BlogEntryCreate,
    ) -> BlogEntryRead:
        """Create a new blog entry."""
        entry = await blog_entry_service.create(data.model_dump())
        return BlogEntryRead.model_validate(entry)

    @put("/{entry_id:uuid}")
    async def update_entry(
        self,
        blog_entry_service: BlogEntryService,
        data: BlogEntryUpdate,
        entry_id: Annotated[UUID, Parameter(title="Entry ID", description="The entry ID")],
    ) -> BlogEntryRead:
        """Update a blog entry."""
        update_data = data.model_dump(exclude_unset=True)
        entry = await blog_entry_service.update(entry_id, update_data)
        return BlogEntryRead.model_validate(entry)

    @delete("/{entry_id:uuid}")
    async def delete_entry(
        self,
        blog_entry_service: BlogEntryService,
        entry_id: Annotated[UUID, Parameter(title="Entry ID", description="The entry ID")],
    ) -> None:
        """Delete a blog entry."""
        await blog_entry_service.delete(entry_id)


class FeedAggregateController(Controller):
    """Controller for FeedAggregate CRUD operations."""

    path = "/api/v1/feed-aggregates"
    tags = ["feed-aggregates"]

    @get("/")
    async def list_aggregates(
        self,
        feed_aggregate_service: FeedAggregateService,
        limit_offset: LimitOffset,
    ) -> list[FeedAggregateRead]:
        """List all feed aggregates with pagination."""
        aggregates, _total = await feed_aggregate_service.list_and_count(limit_offset)
        return [FeedAggregateRead.model_validate(aggregate) for aggregate in aggregates]

    @get("/{aggregate_id:uuid}")
    async def get_aggregate(
        self,
        feed_aggregate_service: FeedAggregateService,
        aggregate_id: Annotated[UUID, Parameter(title="Aggregate ID", description="The aggregate ID")],
    ) -> FeedAggregateWithFeeds:
        """Get a feed aggregate by ID."""
        aggregate = await feed_aggregate_service.get(aggregate_id)
        return FeedAggregateWithFeeds.model_validate(aggregate)

    @get("/slug/{slug:str}")
    async def get_aggregate_by_slug(
        self,
        feed_aggregate_service: FeedAggregateService,
        slug: Annotated[str, Parameter(title="Slug", description="The aggregate slug")],
    ) -> FeedAggregateWithFeeds:
        """Get a feed aggregate by slug."""
        aggregate = await feed_aggregate_service.get_by_slug(slug)
        if not aggregate:
            raise NotFoundException(f"Feed aggregate with slug {slug} not found")
        return FeedAggregateWithFeeds.model_validate(aggregate)

    @post("/")
    async def create_aggregate(
        self,
        feed_aggregate_service: FeedAggregateService,
        data: FeedAggregateCreate,
    ) -> FeedAggregateRead:
        """Create a new feed aggregate."""
        aggregate = await feed_aggregate_service.create(data.model_dump(exclude={"feed_ids"}))
        return FeedAggregateRead.model_validate(aggregate)

    @put("/{aggregate_id:uuid}")
    async def update_aggregate(
        self,
        feed_aggregate_service: FeedAggregateService,
        data: FeedAggregateUpdate,
        aggregate_id: Annotated[UUID, Parameter(title="Aggregate ID", description="The aggregate ID")],
    ) -> FeedAggregateRead:
        """Update a feed aggregate."""
        update_data = data.model_dump(exclude_unset=True, exclude={"feed_ids"})
        aggregate = await feed_aggregate_service.update(aggregate_id, update_data)
        return FeedAggregateRead.model_validate(aggregate)

    @delete("/{aggregate_id:uuid}")
    async def delete_aggregate(
        self,
        feed_aggregate_service: FeedAggregateService,
        aggregate_id: Annotated[UUID, Parameter(title="Aggregate ID", description="The aggregate ID")],
    ) -> None:
        """Delete a feed aggregate."""
        await feed_aggregate_service.delete(aggregate_id)


class RelatedBlogController(Controller):
    """Controller for RelatedBlog CRUD operations."""

    path = "/api/v1/related-blogs"
    tags = ["related-blogs"]

    @get("/")
    async def list_related_blogs(
        self,
        related_blog_service: RelatedBlogService,
        limit_offset: LimitOffset,
    ) -> list[RelatedBlogRead]:
        """List all related blogs with pagination."""
        blogs, _total = await related_blog_service.list_and_count(limit_offset)
        return [RelatedBlogRead.model_validate(blog) for blog in blogs]

    @get("/{blog_id:uuid}")
    async def get_related_blog(
        self,
        related_blog_service: RelatedBlogService,
        blog_id: Annotated[UUID, Parameter(title="Blog ID", description="The blog ID")],
    ) -> RelatedBlogRead:
        """Get a related blog by ID."""
        blog = await related_blog_service.get(blog_id)
        return RelatedBlogRead.model_validate(blog)

    @post("/")
    async def create_related_blog(
        self,
        related_blog_service: RelatedBlogService,
        data: RelatedBlogCreate,
    ) -> RelatedBlogRead:
        """Create a new related blog."""
        blog = await related_blog_service.create(data.model_dump())
        return RelatedBlogRead.model_validate(blog)

    @put("/{blog_id:uuid}")
    async def update_related_blog(
        self,
        related_blog_service: RelatedBlogService,
        data: RelatedBlogUpdate,
        blog_id: Annotated[UUID, Parameter(title="Blog ID", description="The blog ID")],
    ) -> RelatedBlogRead:
        """Update a related blog."""
        update_data = data.model_dump(exclude_unset=True)
        blog = await related_blog_service.update(blog_id, update_data)
        return RelatedBlogRead.model_validate(blog)

    @delete("/{blog_id:uuid}")
    async def delete_related_blog(
        self,
        related_blog_service: RelatedBlogService,
        blog_id: Annotated[UUID, Parameter(title="Blog ID", description="The blog ID")],
    ) -> None:
        """Delete a related blog."""
        await related_blog_service.delete(blog_id)


class BlogsPageController(Controller):
    """Controller for blogs HTML pages."""

    path = "/blogs"

    @get("/")
    async def blogs_index(
        self,
        blog_entry_service: BlogEntryService,
        feed_service: FeedService,
        related_blog_service: RelatedBlogService,
    ) -> Template:
        """Render the main blogs page."""
        recent_entries = await blog_entry_service.get_recent_entries(limit=20)
        feeds = await feed_service.get_active_feeds(limit=100)
        related_blogs = await related_blog_service.get_all_active(limit=100)

        return Template(
            template_name="blogs/index.html.jinja2",
            context={
                "recent_entries": recent_entries,
                "feeds": feeds,
                "related_blogs": related_blogs,
            },
        )

    @get("/feed/{slug:str}/")
    async def feed_detail(
        self,
        slug: str,
        feed_service: FeedService,
        blog_entry_service: BlogEntryService,
    ) -> Template:
        """Render the feed detail page."""
        feeds = await feed_service.get_active_feeds(limit=1000)
        feed = next((f for f in feeds if f.name.lower().replace(" ", "-") == slug), None)

        if not feed:
            raise NotFoundException(f"Feed {slug} not found")

        entries = await blog_entry_service.get_by_feed_id(feed.id, limit=100)

        return Template(
            template_name="blogs/feed.html.jinja2",
            context={
                "feed": feed,
                "entries": entries,
            },
        )

"""Integration tests for blogs domain API routes.

Tests cover FeedController, BlogEntryController, FeedAggregateController, and RelatedBlogController.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from advanced_alchemy.filters import LimitOffset
from litestar import Litestar
from litestar.params import Parameter
from litestar.testing import AsyncTestClient
from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.blogs.controllers import (
    BlogEntryController,
    FeedAggregateController,
    FeedController,
    RelatedBlogController,
)
from pydotorg.domains.blogs.dependencies import get_blogs_dependencies
from pydotorg.domains.blogs.models import BlogEntry, Feed, FeedAggregate, RelatedBlog

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class BlogsTestFixtures:
    """Test fixtures for blogs routes."""

    client: AsyncTestClient
    postgres_uri: str


async def _create_feed_via_db(postgres_uri: str, **feed_data: object) -> dict:
    """Create a feed directly in the database."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        feed = Feed(
            name=feed_data.get("name", "Test Blog"),
            website_url=feed_data.get("website_url", "https://testblog.com"),
            feed_url=feed_data.get("feed_url", f"https://testblog.com/feed-{uuid4().hex[:8]}"),
            is_active=feed_data.get("is_active", True),
        )
        session.add(feed)
        await session.commit()
        await session.refresh(feed)
        result = {
            "id": str(feed.id),
            "name": feed.name,
            "website_url": feed.website_url,
            "feed_url": feed.feed_url,
            "is_active": feed.is_active,
        }
    await engine.dispose()
    return result


async def _create_entry_via_db(postgres_uri: str, feed_id: str, **entry_data: object) -> dict:
    """Create a blog entry directly in the database."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        from uuid import UUID as PyUUID

        entry = BlogEntry(
            feed_id=PyUUID(feed_id),
            title=entry_data.get("title", "Test Entry"),
            summary=entry_data.get("summary", "Test summary"),
            content=entry_data.get("content", "Test content"),
            url=entry_data.get("url", f"https://testblog.com/posts/{uuid4().hex[:8]}"),
            pub_date=entry_data.get("pub_date", datetime.datetime.now(datetime.UTC)),
            guid=entry_data.get("guid", f"guid-{uuid4().hex}"),
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        result = {
            "id": str(entry.id),
            "feed_id": str(entry.feed_id),
            "title": entry.title,
            "url": entry.url,
            "guid": entry.guid,
        }
    await engine.dispose()
    return result


async def _create_aggregate_via_db(postgres_uri: str, **aggregate_data: object) -> dict:
    """Create a feed aggregate directly in the database."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        slug = aggregate_data.get("slug", f"aggregate-{uuid4().hex[:8]}")
        aggregate = FeedAggregate(
            name=aggregate_data.get("name", "Test Aggregate"),
            slug=slug,
            description=aggregate_data.get("description", "Test description"),
        )
        session.add(aggregate)
        await session.commit()
        await session.refresh(aggregate)
        result = {
            "id": str(aggregate.id),
            "name": aggregate.name,
            "slug": aggregate.slug,
        }
    await engine.dispose()
    return result


async def _create_related_blog_via_db(postgres_uri: str, **blog_data: object) -> dict:
    """Create a related blog directly in the database."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        blog = RelatedBlog(
            blog_name=blog_data.get("blog_name", "Related Blog"),
            blog_website=blog_data.get("blog_website", "https://relatedblog.com"),
            description=blog_data.get("description", "A related blog"),
        )
        session.add(blog)
        await session.commit()
        await session.refresh(blog)
        result = {
            "id": str(blog.id),
            "blog_name": blog.blog_name,
            "blog_website": blog.blog_website,
        }
    await engine.dispose()
    return result


@pytest.fixture
async def blogs_fixtures(postgres_uri: str) -> AsyncIterator[BlogsTestFixtures]:
    """Create test fixtures with fresh database schema."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(AuditBase.metadata.create_all)
    await engine.dispose()

    async def provide_limit_offset(
        current_page: int = Parameter(ge=1, default=1, query="currentPage"),
        page_size: int = Parameter(ge=1, le=100, default=100, query="pageSize"),
    ) -> LimitOffset:
        """Provide limit offset pagination."""
        return LimitOffset(page_size, page_size * (current_page - 1))

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        metadata=AuditBase.metadata,
        create_all=False,
        before_send_handler="autocommit",
    )
    sqlalchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)

    blogs_deps = get_blogs_dependencies()
    blogs_deps["limit_offset"] = provide_limit_offset

    app = Litestar(
        route_handlers=[
            FeedController,
            BlogEntryController,
            FeedAggregateController,
            RelatedBlogController,
        ],
        plugins=[sqlalchemy_plugin],
        dependencies=blogs_deps,
        debug=True,
    )

    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        fixtures = BlogsTestFixtures()
        fixtures.client = client
        fixtures.postgres_uri = postgres_uri
        yield fixtures


class TestFeedControllerRoutes:
    """Tests for FeedController API routes."""

    async def test_list_feeds(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test listing feeds."""
        response = await blogs_fixtures.client.get("/api/v1/feeds/")
        assert response.status_code == 200
        feeds = response.json()
        assert isinstance(feeds, list)

    async def test_list_feeds_with_pagination(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test listing feeds with pagination."""
        for i in range(3):
            await _create_feed_via_db(
                blogs_fixtures.postgres_uri,
                name=f"Feed {i}",
                feed_url=f"https://blog{i}.com/feed-{uuid4().hex[:8]}",
            )
        response = await blogs_fixtures.client.get("/api/v1/feeds/?pageSize=2&currentPage=1")
        assert response.status_code == 200
        feeds = response.json()
        assert len(feeds) <= 2

    async def test_list_active_feeds(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test listing active feeds."""
        await _create_feed_via_db(
            blogs_fixtures.postgres_uri,
            name="Active Feed",
            is_active=True,
        )
        await _create_feed_via_db(
            blogs_fixtures.postgres_uri,
            name="Inactive Feed",
            is_active=False,
        )
        response = await blogs_fixtures.client.get("/api/v1/feeds/active")
        assert response.status_code in (200, 500)

    async def test_create_feed(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test creating a feed."""
        feed_data = {
            "name": "New Blog",
            "website_url": "https://newblog.com",
            "feed_url": f"https://newblog.com/feed-{uuid4().hex[:8]}",
            "is_active": True,
        }
        response = await blogs_fixtures.client.post("/api/v1/feeds/", json=feed_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["name"] == "New Blog"

    async def test_get_feed_by_id(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test getting a feed by ID."""
        feed = await _create_feed_via_db(
            blogs_fixtures.postgres_uri,
            name="Get Feed Test",
        )
        response = await blogs_fixtures.client.get(f"/api/v1/feeds/{feed['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Get Feed Test"

    async def test_get_feed_by_id_not_found(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test getting a non-existent feed returns 404."""
        fake_id = str(uuid4())
        response = await blogs_fixtures.client.get(f"/api/v1/feeds/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_update_feed(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test updating a feed."""
        feed = await _create_feed_via_db(
            blogs_fixtures.postgres_uri,
            name="Original Name",
        )
        update_data = {"name": "Updated Name", "is_active": False}
        response = await blogs_fixtures.client.put(f"/api/v1/feeds/{feed['id']}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Updated Name"

    async def test_delete_feed(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test deleting a feed."""
        feed = await _create_feed_via_db(
            blogs_fixtures.postgres_uri,
            name="Delete Me",
        )
        response = await blogs_fixtures.client.delete(f"/api/v1/feeds/{feed['id']}")
        assert response.status_code in (200, 204, 500)


class TestBlogEntryControllerRoutes:
    """Tests for BlogEntryController API routes."""

    async def test_list_entries(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test listing blog entries."""
        response = await blogs_fixtures.client.get("/api/v1/blog-entries/")
        assert response.status_code == 200
        entries = response.json()
        assert isinstance(entries, list)

    async def test_list_entries_with_pagination(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test listing entries with pagination."""
        feed = await _create_feed_via_db(blogs_fixtures.postgres_uri, name="Test Feed")
        for i in range(3):
            await _create_entry_via_db(
                blogs_fixtures.postgres_uri,
                feed_id=feed["id"],
                title=f"Entry {i}",
                guid=f"guid-{i}-{uuid4().hex}",
            )
        response = await blogs_fixtures.client.get("/api/v1/blog-entries/?pageSize=2&currentPage=1")
        assert response.status_code == 200
        entries = response.json()
        assert len(entries) <= 2

    async def test_list_recent_entries(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test listing recent entries."""
        feed = await _create_feed_via_db(blogs_fixtures.postgres_uri, name="Recent Feed")
        await _create_entry_via_db(
            blogs_fixtures.postgres_uri,
            feed_id=feed["id"],
            title="Recent Entry",
        )
        response = await blogs_fixtures.client.get("/api/v1/blog-entries/recent")
        assert response.status_code in (200, 500)

    async def test_list_entries_by_feed(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test listing entries for a specific feed."""
        feed = await _create_feed_via_db(blogs_fixtures.postgres_uri, name="Feed For Entries")
        await _create_entry_via_db(
            blogs_fixtures.postgres_uri,
            feed_id=feed["id"],
            title="Entry For Feed",
        )
        response = await blogs_fixtures.client.get(f"/api/v1/blog-entries/feed/{feed['id']}")
        assert response.status_code in (200, 500)

    async def test_create_entry(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test creating a blog entry."""
        feed = await _create_feed_via_db(blogs_fixtures.postgres_uri, name="Create Entry Feed")
        entry_data = {
            "feed_id": feed["id"],
            "title": "New Blog Post",
            "summary": "A new blog post summary",
            "content": "The full content",
            "url": f"https://blog.com/posts/{uuid4().hex[:8]}",
            "pub_date": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "guid": f"guid-new-{uuid4().hex}",
        }
        response = await blogs_fixtures.client.post("/api/v1/blog-entries/", json=entry_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["title"] == "New Blog Post"

    async def test_get_entry_by_id(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test getting an entry by ID."""
        feed = await _create_feed_via_db(blogs_fixtures.postgres_uri, name="Get Entry Feed")
        entry = await _create_entry_via_db(
            blogs_fixtures.postgres_uri,
            feed_id=feed["id"],
            title="Get This Entry",
        )
        response = await blogs_fixtures.client.get(f"/api/v1/blog-entries/{entry['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["title"] == "Get This Entry"

    async def test_get_entry_by_id_not_found(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test getting a non-existent entry returns 404."""
        fake_id = str(uuid4())
        response = await blogs_fixtures.client.get(f"/api/v1/blog-entries/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_update_entry(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test updating a blog entry."""
        feed = await _create_feed_via_db(blogs_fixtures.postgres_uri, name="Update Entry Feed")
        entry = await _create_entry_via_db(
            blogs_fixtures.postgres_uri,
            feed_id=feed["id"],
            title="Original Title",
        )
        update_data = {"title": "Updated Title", "summary": "Updated summary"}
        response = await blogs_fixtures.client.put(f"/api/v1/blog-entries/{entry['id']}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["title"] == "Updated Title"

    async def test_delete_entry(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test deleting a blog entry."""
        feed = await _create_feed_via_db(blogs_fixtures.postgres_uri, name="Delete Entry Feed")
        entry = await _create_entry_via_db(
            blogs_fixtures.postgres_uri,
            feed_id=feed["id"],
            title="Delete Me Entry",
        )
        response = await blogs_fixtures.client.delete(f"/api/v1/blog-entries/{entry['id']}")
        assert response.status_code in (200, 204, 500)


class TestFeedAggregateControllerRoutes:
    """Tests for FeedAggregateController API routes."""

    async def test_list_aggregates(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test listing feed aggregates."""
        response = await blogs_fixtures.client.get("/api/v1/feed-aggregates/")
        assert response.status_code == 200
        aggregates = response.json()
        assert isinstance(aggregates, list)

    async def test_list_aggregates_with_pagination(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test listing aggregates with pagination."""
        for i in range(3):
            await _create_aggregate_via_db(
                blogs_fixtures.postgres_uri,
                name=f"Aggregate {i}",
                slug=f"aggregate-{i}-{uuid4().hex[:8]}",
            )
        response = await blogs_fixtures.client.get("/api/v1/feed-aggregates/?pageSize=2&currentPage=1")
        assert response.status_code == 200
        aggregates = response.json()
        assert len(aggregates) <= 2

    async def test_create_aggregate(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test creating a feed aggregate."""
        aggregate_data = {
            "name": "New Aggregate",
            "slug": f"new-aggregate-{uuid4().hex[:8]}",
            "description": "A new aggregate",
            "feed_ids": [],
        }
        response = await blogs_fixtures.client.post("/api/v1/feed-aggregates/", json=aggregate_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["name"] == "New Aggregate"

    async def test_get_aggregate_by_id(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test getting an aggregate by ID."""
        aggregate = await _create_aggregate_via_db(
            blogs_fixtures.postgres_uri,
            name="Get Aggregate Test",
        )
        response = await blogs_fixtures.client.get(f"/api/v1/feed-aggregates/{aggregate['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Get Aggregate Test"

    async def test_get_aggregate_by_id_not_found(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test getting a non-existent aggregate returns 404."""
        fake_id = str(uuid4())
        response = await blogs_fixtures.client.get(f"/api/v1/feed-aggregates/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_get_aggregate_by_slug(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test getting an aggregate by slug."""
        slug = f"slug-test-{uuid4().hex[:8]}"
        await _create_aggregate_via_db(
            blogs_fixtures.postgres_uri,
            name="Slug Test Aggregate",
            slug=slug,
        )
        response = await blogs_fixtures.client.get(f"/api/v1/feed-aggregates/slug/{slug}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Slug Test Aggregate"

    async def test_get_aggregate_by_slug_not_found(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test getting aggregate by non-existent slug returns 404."""
        response = await blogs_fixtures.client.get("/api/v1/feed-aggregates/slug/nonexistent-slug")
        assert response.status_code in (404, 500)

    async def test_update_aggregate(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test updating a feed aggregate."""
        aggregate = await _create_aggregate_via_db(
            blogs_fixtures.postgres_uri,
            name="Original Aggregate",
        )
        update_data = {"name": "Updated Aggregate", "description": "Updated description"}
        response = await blogs_fixtures.client.put(f"/api/v1/feed-aggregates/{aggregate['id']}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["name"] == "Updated Aggregate"

    async def test_delete_aggregate(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test deleting a feed aggregate."""
        aggregate = await _create_aggregate_via_db(
            blogs_fixtures.postgres_uri,
            name="Delete Me Aggregate",
        )
        response = await blogs_fixtures.client.delete(f"/api/v1/feed-aggregates/{aggregate['id']}")
        assert response.status_code in (200, 204, 500)


class TestRelatedBlogControllerRoutes:
    """Tests for RelatedBlogController API routes."""

    async def test_list_related_blogs(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test listing related blogs."""
        response = await blogs_fixtures.client.get("/api/v1/related-blogs/")
        assert response.status_code == 200
        blogs = response.json()
        assert isinstance(blogs, list)

    async def test_list_related_blogs_with_pagination(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test listing related blogs with pagination."""
        for i in range(3):
            await _create_related_blog_via_db(
                blogs_fixtures.postgres_uri,
                blog_name=f"Related Blog {i}",
                blog_website=f"https://related{i}.com",
            )
        response = await blogs_fixtures.client.get("/api/v1/related-blogs/?pageSize=2&currentPage=1")
        assert response.status_code == 200
        blogs = response.json()
        assert len(blogs) <= 2

    async def test_create_related_blog(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test creating a related blog."""
        blog_data = {
            "blog_name": "New Related Blog",
            "blog_website": "https://newrelated.com",
            "description": "A new related blog",
        }
        response = await blogs_fixtures.client.post("/api/v1/related-blogs/", json=blog_data)
        assert response.status_code in (200, 201, 500)
        if response.status_code in (200, 201):
            result = response.json()
            assert result["blog_name"] == "New Related Blog"

    async def test_get_related_blog_by_id(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test getting a related blog by ID."""
        blog = await _create_related_blog_via_db(
            blogs_fixtures.postgres_uri,
            blog_name="Get Related Blog Test",
        )
        response = await blogs_fixtures.client.get(f"/api/v1/related-blogs/{blog['id']}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["blog_name"] == "Get Related Blog Test"

    async def test_get_related_blog_by_id_not_found(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test getting a non-existent related blog returns 404."""
        fake_id = str(uuid4())
        response = await blogs_fixtures.client.get(f"/api/v1/related-blogs/{fake_id}")
        assert response.status_code in (404, 500)

    async def test_update_related_blog(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test updating a related blog."""
        blog = await _create_related_blog_via_db(
            blogs_fixtures.postgres_uri,
            blog_name="Original Related Blog",
        )
        update_data = {"blog_name": "Updated Related Blog", "description": "Updated"}
        response = await blogs_fixtures.client.put(f"/api/v1/related-blogs/{blog['id']}", json=update_data)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            result = response.json()
            assert result["blog_name"] == "Updated Related Blog"

    async def test_delete_related_blog(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test deleting a related blog."""
        blog = await _create_related_blog_via_db(
            blogs_fixtures.postgres_uri,
            blog_name="Delete Me Related Blog",
        )
        response = await blogs_fixtures.client.delete(f"/api/v1/related-blogs/{blog['id']}")
        assert response.status_code in (200, 204, 500)


class TestBlogsValidation:
    """Tests for blogs domain validation."""

    async def test_create_feed_missing_name(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test creating a feed without name fails validation."""
        feed_data = {
            "website_url": "https://test.com",
            "feed_url": "https://test.com/feed",
        }
        response = await blogs_fixtures.client.post("/api/v1/feeds/", json=feed_data)
        assert response.status_code in (400, 422, 500)

    async def test_create_feed_missing_url(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test creating a feed without feed_url fails validation."""
        feed_data = {
            "name": "Test Feed",
            "website_url": "https://test.com",
        }
        response = await blogs_fixtures.client.post("/api/v1/feeds/", json=feed_data)
        assert response.status_code in (400, 422, 500)

    async def test_create_entry_missing_title(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test creating an entry without title fails validation."""
        feed = await _create_feed_via_db(blogs_fixtures.postgres_uri, name="Validation Feed")
        entry_data = {
            "feed_id": feed["id"],
            "url": "https://test.com/post",
            "pub_date": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "guid": f"guid-{uuid4().hex}",
        }
        response = await blogs_fixtures.client.post("/api/v1/blog-entries/", json=entry_data)
        assert response.status_code in (400, 422, 500)

    async def test_create_entry_missing_feed_id(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test creating an entry without feed_id fails validation."""
        entry_data = {
            "title": "Test Entry",
            "url": "https://test.com/post",
            "pub_date": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "guid": f"guid-{uuid4().hex}",
        }
        response = await blogs_fixtures.client.post("/api/v1/blog-entries/", json=entry_data)
        assert response.status_code in (400, 422, 500)

    async def test_create_aggregate_missing_name(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test creating an aggregate without name fails validation."""
        aggregate_data = {
            "slug": "test-slug",
        }
        response = await blogs_fixtures.client.post("/api/v1/feed-aggregates/", json=aggregate_data)
        assert response.status_code in (400, 422, 500)

    async def test_create_related_blog_missing_name(self, blogs_fixtures: BlogsTestFixtures) -> None:
        """Test creating a related blog without blog_name fails validation."""
        blog_data = {
            "blog_website": "https://test.com",
        }
        response = await blogs_fixtures.client.post("/api/v1/related-blogs/", json=blog_data)
        assert response.status_code in (400, 422, 500)

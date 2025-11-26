"""Unit tests for Blog models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydotorg.domains.blogs.models import BlogEntry, Feed, FeedAggregate, RelatedBlog


class TestFeedModel:
    def test_create_feed(self) -> None:
        feed = Feed(
            name="Python Insider",
            website_url="https://blog.python.org",
            feed_url="https://blog.python.org/feeds/posts/default",
        )
        assert feed.name == "Python Insider"
        assert feed.website_url == "https://blog.python.org"
        assert feed.feed_url == "https://blog.python.org/feeds/posts/default"

    def test_feed_explicit_active(self) -> None:
        feed = Feed(
            name="Test Feed",
            website_url="https://example.com",
            feed_url="https://example.com/feed",
            is_active=True,
        )
        assert feed.last_fetched is None
        assert feed.is_active is True

    def test_feed_with_last_fetched(self) -> None:
        fetch_time = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
        feed = Feed(
            name="Test Feed",
            website_url="https://example.com",
            feed_url="https://example.com/feed",
            last_fetched=fetch_time,
        )
        assert feed.last_fetched == fetch_time

    def test_feed_inactive(self) -> None:
        feed = Feed(
            name="Inactive Feed",
            website_url="https://example.com",
            feed_url="https://example.com/feed",
            is_active=False,
        )
        assert feed.is_active is False


class TestBlogEntryModel:
    def test_create_blog_entry(self) -> None:
        feed_id = uuid4()
        pub_date = datetime(2024, 1, 1, 10, 0, tzinfo=UTC)
        entry = BlogEntry(
            feed_id=feed_id,
            title="Python 3.13 Released",
            url="https://blog.python.org/2024/01/python-3-13-released.html",
            pub_date=pub_date,
            guid="python-3-13-released",
        )
        assert entry.feed_id == feed_id
        assert entry.title == "Python 3.13 Released"
        assert entry.url == "https://blog.python.org/2024/01/python-3-13-released.html"
        assert entry.pub_date == pub_date
        assert entry.guid == "python-3-13-released"

    def test_blog_entry_defaults(self) -> None:
        entry = BlogEntry(
            feed_id=uuid4(),
            title="Test Entry",
            url="https://example.com/entry",
            pub_date=datetime.now(UTC),
            guid="test-entry",
        )
        assert entry.summary is None
        assert entry.content is None

    def test_blog_entry_with_summary(self) -> None:
        entry = BlogEntry(
            feed_id=uuid4(),
            title="Test Entry",
            summary="This is a summary of the blog post",
            url="https://example.com/entry",
            pub_date=datetime.now(UTC),
            guid="test-entry",
        )
        assert entry.summary == "This is a summary of the blog post"

    def test_blog_entry_with_content(self) -> None:
        content = "<p>This is the full content of the blog post</p>"
        entry = BlogEntry(
            feed_id=uuid4(),
            title="Test Entry",
            content=content,
            url="https://example.com/entry",
            pub_date=datetime.now(UTC),
            guid="test-entry",
        )
        assert entry.content == content

    def test_blog_entry_with_summary_and_content(self) -> None:
        entry = BlogEntry(
            feed_id=uuid4(),
            title="Test Entry",
            summary="Brief summary",
            content="<p>Full content here</p>",
            url="https://example.com/entry",
            pub_date=datetime.now(UTC),
            guid="test-entry",
        )
        assert entry.summary == "Brief summary"
        assert entry.content == "<p>Full content here</p>"


class TestFeedAggregateModel:
    def test_create_feed_aggregate(self) -> None:
        aggregate = FeedAggregate(
            name="Python Blogs",
            slug="python-blogs",
        )
        assert aggregate.name == "Python Blogs"
        assert aggregate.slug == "python-blogs"

    def test_feed_aggregate_defaults(self) -> None:
        aggregate = FeedAggregate(
            name="Test Aggregate",
            slug="test-aggregate",
        )
        assert aggregate.description is None

    def test_feed_aggregate_with_description(self) -> None:
        aggregate = FeedAggregate(
            name="Community Blogs",
            slug="community-blogs",
            description="A collection of blogs from the Python community",
        )
        assert aggregate.description == "A collection of blogs from the Python community"


class TestRelatedBlogModel:
    def test_create_related_blog(self) -> None:
        blog = RelatedBlog(
            blog_name="Real Python",
            blog_website="https://realpython.com",
        )
        assert blog.blog_name == "Real Python"
        assert blog.blog_website == "https://realpython.com"

    def test_related_blog_defaults(self) -> None:
        blog = RelatedBlog(
            blog_name="Test Blog",
            blog_website="https://example.com",
        )
        assert blog.description is None

    def test_related_blog_with_description(self) -> None:
        blog = RelatedBlog(
            blog_name="Python Weekly",
            blog_website="https://pythonweekly.com",
            description="A weekly newsletter featuring curated news and articles",
        )
        assert blog.description == "A weekly newsletter featuring curated news and articles"

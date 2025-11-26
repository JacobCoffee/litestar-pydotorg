"""Blogs domain dependency injection providers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.domains.blogs.repositories import (
    BlogEntryRepository,
    FeedAggregateRepository,
    FeedRepository,
    RelatedBlogRepository,
)
from pydotorg.domains.blogs.services import BlogEntryService, FeedAggregateService, FeedService, RelatedBlogService


async def provide_feed_repository(db_session: AsyncSession) -> FeedRepository:
    """Provide a FeedRepository instance."""
    return FeedRepository(session=db_session)


async def provide_feed_service(db_session: AsyncSession) -> FeedService:
    """Provide a FeedService instance."""
    return FeedService(session=db_session)


async def provide_blog_entry_repository(db_session: AsyncSession) -> BlogEntryRepository:
    """Provide a BlogEntryRepository instance."""
    return BlogEntryRepository(session=db_session)


async def provide_blog_entry_service(db_session: AsyncSession) -> BlogEntryService:
    """Provide a BlogEntryService instance."""
    return BlogEntryService(session=db_session)


async def provide_feed_aggregate_repository(db_session: AsyncSession) -> FeedAggregateRepository:
    """Provide a FeedAggregateRepository instance."""
    return FeedAggregateRepository(session=db_session)


async def provide_feed_aggregate_service(db_session: AsyncSession) -> FeedAggregateService:
    """Provide a FeedAggregateService instance."""
    return FeedAggregateService(session=db_session)


async def provide_related_blog_repository(db_session: AsyncSession) -> RelatedBlogRepository:
    """Provide a RelatedBlogRepository instance."""
    return RelatedBlogRepository(session=db_session)


async def provide_related_blog_service(db_session: AsyncSession) -> RelatedBlogService:
    """Provide a RelatedBlogService instance."""
    return RelatedBlogService(session=db_session)


def get_blogs_dependencies() -> dict:
    """Get all blogs domain dependency providers."""
    return {
        "feed_repository": provide_feed_repository,
        "feed_service": provide_feed_service,
        "blog_entry_repository": provide_blog_entry_repository,
        "blog_entry_service": provide_blog_entry_service,
        "feed_aggregate_repository": provide_feed_aggregate_repository,
        "feed_aggregate_service": provide_feed_aggregate_service,
        "related_blog_repository": provide_related_blog_repository,
        "related_blog_service": provide_related_blog_service,
    }

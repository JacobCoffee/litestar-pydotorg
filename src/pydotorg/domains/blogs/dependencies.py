"""Blogs domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.blogs.repositories import (
    BlogEntryRepository,
    FeedAggregateRepository,
    FeedRepository,
    RelatedBlogRepository,
)
from pydotorg.domains.blogs.services import BlogEntryService, FeedAggregateService, FeedService, RelatedBlogService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_feed_repository(db_session: AsyncSession) -> AsyncGenerator[FeedRepository, None]:
    """Provide a FeedRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A FeedRepository instance.
    """
    async with FeedRepository(session=db_session) as repo:
        yield repo


async def provide_feed_service(
    feed_repository: FeedRepository,
) -> AsyncGenerator[FeedService, None]:
    """Provide a FeedService instance.

    Args:
        feed_repository: The feed repository.

    Yields:
        A FeedService instance.
    """
    async with FeedService(repository=feed_repository) as service:
        yield service


async def provide_blog_entry_repository(db_session: AsyncSession) -> AsyncGenerator[BlogEntryRepository, None]:
    """Provide a BlogEntryRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A BlogEntryRepository instance.
    """
    async with BlogEntryRepository(session=db_session) as repo:
        yield repo


async def provide_blog_entry_service(
    blog_entry_repository: BlogEntryRepository,
) -> AsyncGenerator[BlogEntryService, None]:
    """Provide a BlogEntryService instance.

    Args:
        blog_entry_repository: The blog entry repository.

    Yields:
        A BlogEntryService instance.
    """
    async with BlogEntryService(repository=blog_entry_repository) as service:
        yield service


async def provide_feed_aggregate_repository(
    db_session: AsyncSession,
) -> AsyncGenerator[FeedAggregateRepository, None]:
    """Provide a FeedAggregateRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A FeedAggregateRepository instance.
    """
    async with FeedAggregateRepository(session=db_session) as repo:
        yield repo


async def provide_feed_aggregate_service(
    feed_aggregate_repository: FeedAggregateRepository,
) -> AsyncGenerator[FeedAggregateService, None]:
    """Provide a FeedAggregateService instance.

    Args:
        feed_aggregate_repository: The feed aggregate repository.

    Yields:
        A FeedAggregateService instance.
    """
    async with FeedAggregateService(repository=feed_aggregate_repository) as service:
        yield service


async def provide_related_blog_repository(
    db_session: AsyncSession,
) -> AsyncGenerator[RelatedBlogRepository, None]:
    """Provide a RelatedBlogRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A RelatedBlogRepository instance.
    """
    async with RelatedBlogRepository(session=db_session) as repo:
        yield repo


async def provide_related_blog_service(
    related_blog_repository: RelatedBlogRepository,
) -> AsyncGenerator[RelatedBlogService, None]:
    """Provide a RelatedBlogService instance.

    Args:
        related_blog_repository: The related blog repository.

    Yields:
        A RelatedBlogService instance.
    """
    async with RelatedBlogService(repository=related_blog_repository) as service:
        yield service


def get_blogs_dependencies() -> dict:
    """Get all blogs domain dependency providers.

    Returns:
        Dictionary of dependency providers for the blogs domain.
    """
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

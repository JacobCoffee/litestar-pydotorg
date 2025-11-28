"""Database session management with lazy initialization.

This module provides database engine and session factory with lazy initialization
to avoid creating connections at import time. This is critical for worker processes
that manage their own database connections.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pydotorg.config import settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncEngine


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Get or create the async database engine (lazy singleton)."""
    return create_async_engine(
        str(settings.database_url),
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        echo=settings.debug,
    )


@lru_cache(maxsize=1)
def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory (lazy singleton)."""
    return async_sessionmaker(
        get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Yield a database session."""
    async with get_async_session_factory()() as session:
        yield session


# Backwards compatibility - these are now properties that trigger lazy init
# Prefer using the functions directly for clarity
class _LazyEngine:
    """Lazy proxy for backwards compatibility with `engine` import."""

    def __getattr__(self, name: str):
        return getattr(get_engine(), name)


class _LazySessionFactory:
    """Lazy proxy for backwards compatibility with `async_session_factory` import."""

    def __call__(self, *args, **kwargs):
        return get_async_session_factory()(*args, **kwargs)

    def __getattr__(self, name: str):
        return getattr(get_async_session_factory(), name)


engine = _LazyEngine()
async_session_factory = _LazySessionFactory()

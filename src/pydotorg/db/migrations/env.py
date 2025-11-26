"""Alembic environment configuration for async migrations."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import TYPE_CHECKING

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from pydotorg.config import settings
from pydotorg.core.database.base import AuditBase
from pydotorg.domains.banners.models import Banner  # noqa: F401
from pydotorg.domains.blogs.models import BlogEntry, Feed, FeedAggregate, RelatedBlog  # noqa: F401
from pydotorg.domains.codesamples.models import CodeSample  # noqa: F401
from pydotorg.domains.community.models import Link, Photo, Post, Video  # noqa: F401
from pydotorg.domains.downloads.models import OS, Release, ReleaseFile  # noqa: F401
from pydotorg.domains.events.models import Calendar, Event, EventCategory, EventLocation, EventOccurrence  # noqa: F401
from pydotorg.domains.jobs.models import Job, JobCategory, JobReviewComment, JobType  # noqa: F401
from pydotorg.domains.minutes.models import Minutes  # noqa: F401
from pydotorg.domains.nominations.models import Election, Nomination, Nominee  # noqa: F401
from pydotorg.domains.pages.models import DocumentFile, Image, Page  # noqa: F401
from pydotorg.domains.sponsors.models import Sponsor, Sponsorship, SponsorshipLevel  # noqa: F401
from pydotorg.domains.successstories.models import Story, StoryCategory  # noqa: F401
from pydotorg.domains.users.models import Membership, User, UserGroup  # noqa: F401
from pydotorg.domains.work_groups.models import WorkGroup  # noqa: F401

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = AuditBase.metadata

config.set_main_option("sqlalchemy.url", str(settings.database_url))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the provided connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

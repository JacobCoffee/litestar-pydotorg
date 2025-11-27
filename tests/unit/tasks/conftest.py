"""Shared test fixtures for SAQ background task tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from pydotorg.domains.blogs.models import BlogEntry, Feed
    from pydotorg.domains.jobs.models import Job


@pytest.fixture
def mock_session_maker() -> MagicMock:
    """Mock async session maker for database operations.

    The session_maker is a callable that returns an async context manager.
    We use MagicMock for the callable part and AsyncMock for async operations.
    """
    session = AsyncMock()
    session.execute = AsyncMock()

    context_manager = MagicMock()
    context_manager.__aenter__ = AsyncMock(return_value=session)
    context_manager.__aexit__ = AsyncMock(return_value=None)

    session_maker = MagicMock()
    session_maker.return_value = context_manager
    return session_maker


@pytest.fixture
def mock_ctx(mock_session_maker: AsyncMock) -> dict:
    """Base mock SAQ context with common dependencies."""
    return {
        "session_maker": mock_session_maker,
        "db_session": AsyncMock(),
        "redis": AsyncMock(),
        "logger": MagicMock(),
    }


@pytest.fixture
def mock_feed_service() -> AsyncMock:
    """Mock FeedService for feed-related tests."""
    service = AsyncMock()
    service.get_active_feeds = AsyncMock(return_value=[])
    service.get_feeds_needing_update = AsyncMock(return_value=[])
    service.fetch_feed = AsyncMock(return_value=[])
    service.get = AsyncMock()
    return service


@pytest.fixture
def mock_job_service() -> AsyncMock:
    """Mock JobService for job-related tests."""
    service = AsyncMock()
    service.mark_expired_jobs = AsyncMock(return_value=[])
    service.list_by_status = AsyncMock(return_value=[])
    service.archive_job = AsyncMock()
    service.get = AsyncMock()
    return service


@pytest.fixture
def mock_email_service() -> AsyncMock:
    """Mock EmailService for email-related tests."""
    service = AsyncMock()
    service.send_verification_email = MagicMock()
    service.send_password_reset_email = MagicMock()
    service._create_message = MagicMock()
    service._send_email = MagicMock()
    return service


@pytest.fixture
def mock_search_service() -> AsyncMock:
    """Mock SearchService for search-related tests."""
    service = AsyncMock()
    service.clear_index = AsyncMock()
    service.index_documents = AsyncMock()
    service.update_documents = AsyncMock()
    service.delete_documents = AsyncMock()
    service.create_index = AsyncMock()
    service.configure_index = AsyncMock()
    service.close = AsyncMock()
    return service


@pytest.fixture
def sample_feed() -> Feed:
    """Create a sample Feed instance."""
    from pydotorg.domains.blogs.models import Feed

    return Feed(
        id=uuid4(),
        name="Python Insider",
        website_url="https://blog.python.org",
        feed_url="https://blog.python.org/feeds/posts/default",
        is_active=True,
        last_fetched=None,
    )


@pytest.fixture
def sample_feeds() -> list[Feed]:
    """Create multiple sample Feed instances."""
    from pydotorg.domains.blogs.models import Feed

    return [
        Feed(
            id=uuid4(),
            name="Python Insider",
            website_url="https://blog.python.org",
            feed_url="https://blog.python.org/feeds/posts/default",
            is_active=True,
            last_fetched=None,
        ),
        Feed(
            id=uuid4(),
            name="Real Python",
            website_url="https://realpython.com",
            feed_url="https://realpython.com/feed",
            is_active=True,
            last_fetched=datetime.now(UTC) - timedelta(hours=2),
        ),
        Feed(
            id=uuid4(),
            name="Python Weekly",
            website_url="https://pythonweekly.com",
            feed_url="https://pythonweekly.com/rss",
            is_active=True,
            last_fetched=datetime.now(UTC) - timedelta(minutes=30),
        ),
    ]


@pytest.fixture
def sample_blog_entries() -> list[BlogEntry]:
    """Create sample BlogEntry instances."""
    from pydotorg.domains.blogs.models import BlogEntry

    feed_id = uuid4()
    return [
        BlogEntry(
            id=uuid4(),
            feed_id=feed_id,
            title="Python 3.13 Released",
            url="https://blog.python.org/2024/python-313-released.html",
            summary="Announcing the release of Python 3.13",
            pub_date=datetime.now(UTC) - timedelta(days=1),
        ),
        BlogEntry(
            id=uuid4(),
            feed_id=feed_id,
            title="Type Hints Best Practices",
            url="https://blog.python.org/2024/type-hints-best-practices.html",
            summary="Learn how to use type hints effectively",
            pub_date=datetime.now(UTC) - timedelta(days=2),
        ),
    ]


@pytest.fixture
def sample_job() -> Job:
    """Create a sample Job instance."""
    from pydotorg.domains.jobs.models import Job, JobStatus

    return Job(
        id=uuid4(),
        job_title="Senior Python Developer",
        company_name="Tech Corp",
        description="Great opportunity",
        status=JobStatus.APPROVED,
        created_at=datetime.now(UTC) - timedelta(days=1),
        updated_at=datetime.now(UTC) - timedelta(days=1),
        country="USA",
        email="jobs@techcorp.com",
        telecommuting=False,
    )


@pytest.fixture
def sample_jobs() -> list[Job]:
    """Create multiple sample Job instances."""
    from pydotorg.domains.jobs.models import Job, JobStatus

    now = datetime.now(UTC)
    return [
        Job(
            id=uuid4(),
            job_title="Senior Python Developer",
            company_name="Tech Corp",
            description="Great opportunity",
            status=JobStatus.EXPIRED,
            created_at=now - timedelta(days=95),
            updated_at=now - timedelta(days=5),
            country="USA",
            email="jobs@techcorp.com",
            telecommuting=False,
        ),
        Job(
            id=uuid4(),
            job_title="Django Developer",
            company_name="Web Solutions",
            description="Work on exciting projects",
            status=JobStatus.REJECTED,
            created_at=now - timedelta(days=100),
            updated_at=now - timedelta(days=95),
            country="UK",
            email="jobs@websolutions.com",
            telecommuting=True,
        ),
        Job(
            id=uuid4(),
            job_title="Full Stack Engineer",
            company_name="Startup Inc",
            description="Join our team",
            status=JobStatus.DRAFT,
            created_at=now - timedelta(days=45),
            updated_at=now - timedelta(days=45),
            country="Canada",
            email="jobs@startup.com",
            telecommuting=False,
        ),
    ]

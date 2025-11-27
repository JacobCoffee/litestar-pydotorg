"""Integration tests for TaskAdminService and task wiring."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from pydotorg.domains.admin.services.jobs import JobAdminService
from pydotorg.domains.admin.services.tasks import TaskAdminService
from pydotorg.domains.jobs.models import Job, JobCategory, JobStatus, JobType
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    pass


@pytest.mark.integration
class TestTaskAdminServiceIntegration:
    """Integration tests for TaskAdminService."""

    async def test_service_initialization(self) -> None:
        """Test TaskAdminService can be instantiated."""
        service = TaskAdminService()
        assert service is not None
        assert service._queue is None

    async def test_get_available_tasks(self) -> None:
        """Test getting available task functions."""
        service = TaskAdminService()
        tasks = await service.get_available_tasks()

        assert isinstance(tasks, list)
        assert len(tasks) > 0

        task_names = [t["name"] for t in tasks]
        expected_tasks = [
            "refresh_all_feeds",
            "refresh_stale_feeds",
            "expire_jobs",
            "index_all_jobs",
            "warm_homepage_cache",
        ]
        for expected in expected_tasks:
            assert expected in task_names, f"Expected task {expected} not found"

    async def test_get_queue_info_handles_no_redis(self) -> None:
        """Test queue info gracefully handles Redis connection failure."""
        service = TaskAdminService()
        info = await service.get_queue_info()

        assert isinstance(info, dict)
        assert "name" in info
        assert info.get("error") or "workers" in info

    async def test_get_all_jobs_handles_no_redis(self) -> None:
        """Test getting jobs gracefully handles Redis connection failure."""
        service = TaskAdminService()
        jobs = await service.get_all_jobs()

        assert isinstance(jobs, list)

    async def test_get_stats_handles_no_redis(self) -> None:
        """Test stats gracefully handles Redis connection failure."""
        service = TaskAdminService()
        stats = await service.get_stats()

        assert isinstance(stats, dict)
        assert "available_tasks" in stats
        assert stats["available_tasks"] > 0


@pytest.fixture
async def test_user(postgres_uri: str) -> User:
    """Create a test user."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from pydotorg.core.database.base import AuditBase

    engine = create_async_engine(postgres_uri, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    unique_id = uuid4().hex[:8]
    async with async_session() as session:
        user = User(
            username=f"testuser_{unique_id}",
            email=f"test_{unique_id}@example.com",
            password_hash="hashed_password",
            first_name="Test",
            last_name="User",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        user_id = user.id
        user_email = user.email
        user_username = user.username

    await engine.dispose()

    user.id = user_id
    user.email = user_email
    user.username = user_username
    return user


@pytest.fixture
async def test_job(postgres_uri: str, test_user: User) -> Job:
    """Create a test job."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from pydotorg.core.database.base import AuditBase

    engine = create_async_engine(postgres_uri, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        category = JobCategory(name=f"Engineering_{uuid4().hex[:8]}", slug=f"engineering-{uuid4().hex[:8]}")
        session.add(category)
        await session.flush()

        job_type = JobType(name=f"Full-time_{uuid4().hex[:8]}", slug=f"full-time-{uuid4().hex[:8]}")
        session.add(job_type)
        await session.flush()

        job = Job(
            slug=f"test-job-{uuid4().hex[:8]}",
            creator_id=test_user.id,
            company_name="Test Company",
            job_title="Senior Python Developer",
            country="USA",
            description="Test job description",
            email="jobs@testcompany.com",
            status=JobStatus.REVIEW,
            category_id=category.id,
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        job_id = job.id
        job_slug = job.slug
        job_title = job.job_title
        job_company = job.company_name

    await engine.dispose()

    job.id = job_id
    job.slug = job_slug
    job.job_title = job_title
    job.company_name = job_company
    job.creator = test_user
    return job


@pytest.mark.integration
class TestAuthTaskWiring:
    """Integration tests for auth-related task wiring."""

    @patch("pydotorg.domains.users.auth_controller.enqueue_task")
    async def test_registration_enqueues_verification_email(
        self,
        mock_enqueue: AsyncMock,
        client,
    ) -> None:
        """Test that user registration enqueues verification email task."""
        mock_enqueue.return_value = "job-key-123"

        response = await client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "first_name": "New",
                "last_name": "User",
            },
        )

        assert response.status_code == 201

        mock_enqueue.assert_called_once()
        call_args = mock_enqueue.call_args
        assert call_args[0][0] == "send_verification_email"
        assert call_args[1]["to_email"] == "newuser@example.com"
        assert call_args[1]["username"] == "newuser"
        assert "verification_link" in call_args[1]
        assert "verify-email" in call_args[1]["verification_link"]

    @patch("pydotorg.domains.users.auth_controller.enqueue_task")
    async def test_send_verification_enqueues_email(
        self,
        mock_enqueue: AsyncMock,
        client,
    ) -> None:
        """Test that send-verification endpoint enqueues verification email."""
        mock_enqueue.return_value = "job-key-reg"

        await client.post(
            "/api/auth/register",
            json={
                "username": "verifyuser",
                "email": "verify@example.com",
                "password": "SecurePass123!",
            },
        )

        mock_enqueue.reset_mock()
        mock_enqueue.return_value = "job-key-456"

        response = await client.post(
            "/api/auth/send-verification",
            json={"email": "verify@example.com"},
        )

        assert response.status_code == 201

        mock_enqueue.assert_called_once()
        call_args = mock_enqueue.call_args
        assert call_args[0][0] == "send_verification_email"
        assert call_args[1]["to_email"] == "verify@example.com"

    @patch("pydotorg.domains.users.auth_controller.enqueue_task")
    async def test_forgot_password_enqueues_reset_email(
        self,
        mock_enqueue: AsyncMock,
        client,
    ) -> None:
        """Test that forgot password enqueues password reset email."""
        mock_enqueue.return_value = "job-key-reg"

        await client.post(
            "/api/auth/register",
            json={
                "username": "resetuser",
                "email": "reset@example.com",
                "password": "SecurePass123!",
            },
        )

        mock_enqueue.reset_mock()
        mock_enqueue.return_value = "job-key-789"

        response = await client.post(
            "/api/auth/forgot-password",
            json={"email": "reset@example.com"},
        )

        assert response.status_code == 201

        mock_enqueue.assert_called_once()
        call_args = mock_enqueue.call_args
        assert call_args[0][0] == "send_password_reset_email"
        assert call_args[1]["to_email"] == "reset@example.com"
        assert "reset_link" in call_args[1]


@pytest.mark.integration
class TestJobAdminTaskWiring:
    """Integration tests for job admin task wiring."""

    @patch("pydotorg.domains.admin.services.jobs.enqueue_task")
    async def test_approve_job_enqueues_approval_email(
        self,
        mock_enqueue: AsyncMock,
        postgres_uri: str,
        test_job: Job,
    ) -> None:
        """Test that approving a job enqueues approval email task."""
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        mock_enqueue.return_value = "job-key-approved"

        engine = create_async_engine(postgres_uri, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            service = JobAdminService(session)
            result = await service.approve_job(test_job.id)

            assert result is not None
            assert result.status == JobStatus.APPROVED

            assert mock_enqueue.call_count == 2

            email_call = mock_enqueue.call_args_list[0]
            assert email_call[0][0] == "send_job_approved_email"
            assert email_call[1]["to_email"] == test_job.creator.email
            assert email_call[1]["job_title"] == test_job.job_title
            assert email_call[1]["company_name"] == test_job.company_name
            assert "job_url" in email_call[1]

            index_call = mock_enqueue.call_args_list[1]
            assert index_call[0][0] == "index_job"
            assert "job_id" in index_call[1]

        await engine.dispose()

    @patch("pydotorg.domains.admin.services.jobs.enqueue_task")
    async def test_approve_job_enqueues_search_indexing(
        self,
        mock_enqueue: AsyncMock,
        postgres_uri: str,
        test_job: Job,
    ) -> None:
        """Test that approving a job enqueues search indexing task."""
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        mock_enqueue.return_value = "job-key-index"

        engine = create_async_engine(postgres_uri, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            service = JobAdminService(session)
            await service.approve_job(test_job.id)

            index_calls = [call for call in mock_enqueue.call_args_list if call[0][0] == "index_job"]
            assert len(index_calls) == 1

            index_call = index_calls[0]
            assert index_call[1]["job_id"] == str(test_job.id)

        await engine.dispose()

    @patch("pydotorg.domains.admin.services.jobs.enqueue_task")
    async def test_reject_job_enqueues_rejection_email(
        self,
        mock_enqueue: AsyncMock,
        postgres_uri: str,
        test_job: Job,
    ) -> None:
        """Test that rejecting a job enqueues rejection email task."""
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        mock_enqueue.return_value = "job-key-rejected"

        engine = create_async_engine(postgres_uri, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            service = JobAdminService(session)
            rejection_reason = "Job posting does not meet community standards"
            result = await service.reject_job(test_job.id, reason=rejection_reason)

            assert result is not None
            assert result.status == JobStatus.REJECTED

            mock_enqueue.assert_called_once()
            call_args = mock_enqueue.call_args
            assert call_args[0][0] == "send_job_rejected_email"
            assert call_args[1]["to_email"] == test_job.creator.email
            assert call_args[1]["job_title"] == test_job.job_title
            assert call_args[1]["company_name"] == test_job.company_name
            assert call_args[1]["reason"] == rejection_reason

        await engine.dispose()

    @patch("pydotorg.domains.admin.services.jobs.enqueue_task")
    async def test_reject_job_with_default_reason(
        self,
        mock_enqueue: AsyncMock,
        postgres_uri: str,
        test_job: Job,
    ) -> None:
        """Test that rejecting a job uses default reason when none provided."""
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        mock_enqueue.return_value = "job-key-rejected-default"

        engine = create_async_engine(postgres_uri, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            service = JobAdminService(session)
            await service.reject_job(test_job.id)

            call_args = mock_enqueue.call_args
            assert call_args[1]["reason"] == "Your job posting did not meet our guidelines."

        await engine.dispose()

    @patch("pydotorg.domains.admin.services.jobs.enqueue_task")
    async def test_approve_job_handles_enqueue_failure_gracefully(
        self,
        mock_enqueue: AsyncMock,
        postgres_uri: str,
        test_job: Job,
    ) -> None:
        """Test that job approval continues even if task enqueueing fails."""
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        mock_enqueue.return_value = None

        engine = create_async_engine(postgres_uri, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            service = JobAdminService(session)
            result = await service.approve_job(test_job.id)

            assert result is not None
            assert result.status == JobStatus.APPROVED
            assert mock_enqueue.call_count == 2

        await engine.dispose()

    @patch("pydotorg.domains.admin.services.jobs.enqueue_task")
    async def test_reject_job_handles_enqueue_failure_gracefully(
        self,
        mock_enqueue: AsyncMock,
        postgres_uri: str,
        test_job: Job,
    ) -> None:
        """Test that job rejection continues even if email enqueueing fails."""
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        mock_enqueue.return_value = None

        engine = create_async_engine(postgres_uri, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            service = JobAdminService(session)
            result = await service.reject_job(test_job.id)

            assert result is not None
            assert result.status == JobStatus.REJECTED
            mock_enqueue.assert_called_once()

        await engine.dispose()

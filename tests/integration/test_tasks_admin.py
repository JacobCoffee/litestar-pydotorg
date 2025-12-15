"""Integration tests for TaskAdminService, CronJobService, and task wiring."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from pydotorg.domains.admin.services.cron import CronJobService, _cron_to_human, _parse_cron_schedule
from pydotorg.domains.admin.services.jobs import JobAdminService
from pydotorg.domains.admin.services.tasks import TaskAdminService
from pydotorg.domains.jobs.models import Job, JobCategory, JobStatus, JobType
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


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
async def test_user(async_session_factory: async_sessionmaker) -> User:
    """Create a test user using shared session factory."""
    unique_id = uuid4().hex[:8]
    async with async_session_factory() as session:
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
        return user


@pytest.fixture
async def test_job(async_session_factory: async_sessionmaker, test_user: User) -> Job:
    """Create a test job using shared session factory."""
    async with async_session_factory() as session:
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
        async_session_factory: async_sessionmaker,
        test_job: Job,
        test_user: User,
    ) -> None:
        """Test that approving a job enqueues approval email task."""
        mock_enqueue.return_value = "job-key-approved"

        async with async_session_factory() as session:
            service = JobAdminService(session)
            result = await service.approve_job(test_job.id)

            assert result is not None
            assert result.status == JobStatus.APPROVED

            assert mock_enqueue.call_count == 2

            email_call = mock_enqueue.call_args_list[0]
            assert email_call[0][0] == "send_job_approved_email"
            assert email_call[1]["to_email"] == test_user.email
            assert email_call[1]["job_title"] == test_job.job_title
            assert email_call[1]["company_name"] == test_job.company_name
            assert "job_url" in email_call[1]

            index_call = mock_enqueue.call_args_list[1]
            assert index_call[0][0] == "index_job"
            assert "job_id" in index_call[1]

    @patch("pydotorg.domains.admin.services.jobs.enqueue_task")
    async def test_approve_job_enqueues_search_indexing(
        self,
        mock_enqueue: AsyncMock,
        async_session_factory: async_sessionmaker,
        test_job: Job,
    ) -> None:
        """Test that approving a job enqueues search indexing task."""
        mock_enqueue.return_value = "job-key-index"

        async with async_session_factory() as session:
            service = JobAdminService(session)
            await service.approve_job(test_job.id)

            index_calls = [call for call in mock_enqueue.call_args_list if call[0][0] == "index_job"]
            assert len(index_calls) == 1

            index_call = index_calls[0]
            assert index_call[1]["job_id"] == str(test_job.id)

    @patch("pydotorg.domains.admin.services.jobs.enqueue_task")
    async def test_reject_job_enqueues_rejection_email(
        self,
        mock_enqueue: AsyncMock,
        async_session_factory: async_sessionmaker,
        test_job: Job,
        test_user: User,
    ) -> None:
        """Test that rejecting a job enqueues rejection email task."""
        mock_enqueue.return_value = "job-key-rejected"

        async with async_session_factory() as session:
            service = JobAdminService(session)
            rejection_reason = "Job posting does not meet community standards"
            result = await service.reject_job(test_job.id, reason=rejection_reason)

            assert result is not None
            assert result.status == JobStatus.REJECTED

            mock_enqueue.assert_called_once()
            call_args = mock_enqueue.call_args
            assert call_args[0][0] == "send_job_rejected_email"
            assert call_args[1]["to_email"] == test_user.email
            assert call_args[1]["job_title"] == test_job.job_title
            assert call_args[1]["company_name"] == test_job.company_name
            assert call_args[1]["reason"] == rejection_reason

    @patch("pydotorg.domains.admin.services.jobs.enqueue_task")
    async def test_reject_job_with_default_reason(
        self,
        mock_enqueue: AsyncMock,
        async_session_factory: async_sessionmaker,
        test_job: Job,
    ) -> None:
        """Test that rejecting a job uses default reason when none provided."""
        mock_enqueue.return_value = "job-key-rejected-default"

        async with async_session_factory() as session:
            service = JobAdminService(session)
            await service.reject_job(test_job.id)

            call_args = mock_enqueue.call_args
            assert call_args[1]["reason"] == "Your job posting did not meet our guidelines."

    @patch("pydotorg.domains.admin.services.jobs.enqueue_task")
    async def test_approve_job_handles_enqueue_failure_gracefully(
        self,
        mock_enqueue: AsyncMock,
        async_session_factory: async_sessionmaker,
        test_job: Job,
    ) -> None:
        """Test that job approval continues even if task enqueueing fails."""
        mock_enqueue.return_value = None

        async with async_session_factory() as session:
            service = JobAdminService(session)
            result = await service.approve_job(test_job.id)

            assert result is not None
            assert result.status == JobStatus.APPROVED
            assert mock_enqueue.call_count == 2

    @patch("pydotorg.domains.admin.services.jobs.enqueue_task")
    async def test_reject_job_handles_enqueue_failure_gracefully(
        self,
        mock_enqueue: AsyncMock,
        async_session_factory: async_sessionmaker,
        test_job: Job,
    ) -> None:
        """Test that job rejection continues even if email enqueueing fails."""
        mock_enqueue.return_value = None

        async with async_session_factory() as session:
            service = JobAdminService(session)
            result = await service.reject_job(test_job.id)

            assert result is not None
            assert result.status == JobStatus.REJECTED
            mock_enqueue.assert_called_once()


@pytest.mark.integration
class TestCronHelperFunctions:
    """Tests for cron helper functions."""

    def test_cron_to_human_every_n_minutes(self) -> None:
        """Test cron expression for every N minutes."""
        assert _cron_to_human("*/5 * * * *") == "Every 5 minutes"
        assert _cron_to_human("*/15 * * * *") == "Every 15 minutes"

    def test_cron_to_human_every_n_hours(self) -> None:
        """Test cron expression for every N hours."""
        assert _cron_to_human("0 */2 * * *") == "Every 2 hours"
        assert _cron_to_human("0 */6 * * *") == "Every 6 hours"

    def test_cron_to_human_hourly(self) -> None:
        """Test cron expression for hourly."""
        assert _cron_to_human("0 * * * *") == "Every hour at minute 0"

    def test_cron_to_human_daily(self) -> None:
        """Test cron expression for daily."""
        assert _cron_to_human("0 0 * * *") == "Daily at 0:00"
        assert _cron_to_human("0 6 * * *") == "Daily at 6:00"
        assert _cron_to_human("0 23 * * *") == "Daily at 23:00"

    def test_cron_to_human_weekly(self) -> None:
        """Test cron expression for weekly (Sunday)."""
        assert _cron_to_human("0 0 * * 0") == "Weekly on Sunday at 0:00"
        assert _cron_to_human("0 6 * * 0") == "Weekly on Sunday at 6:00"

    def test_cron_to_human_monthly(self) -> None:
        """Test cron expression for monthly."""
        assert _cron_to_human("0 0 1 * *") == "Monthly on 1st at 0:00"
        assert _cron_to_human("0 6 1 * *") == "Monthly on 1st at 6:00"

    def test_cron_to_human_invalid_format(self) -> None:
        """Test cron expression with invalid format returns original."""
        assert _cron_to_human("invalid") == "invalid"
        assert _cron_to_human("* * *") == "* * *"

    def test_parse_cron_schedule_valid(self) -> None:
        """Test parsing a valid cron schedule."""
        result = _parse_cron_schedule("0 0 * * *")
        assert result["is_valid"] is True
        assert result["next_run"] is not None
        assert result["previous_run"] is not None
        assert result["schedule_description"] == "Daily at 0:00"

    def test_parse_cron_schedule_invalid(self) -> None:
        """Test parsing an invalid cron schedule."""
        result = _parse_cron_schedule("invalid cron")
        assert result["is_valid"] is False
        assert result["next_run"] is None
        assert result["previous_run"] is None


@pytest.mark.integration
class TestCronJobServiceIntegration:
    """Integration tests for CronJobService."""

    async def test_service_initialization(self) -> None:
        """Test CronJobService can be instantiated."""
        service = CronJobService()
        assert service is not None
        assert service._redis is None

    async def test_get_all_cron_jobs(self) -> None:
        """Test getting all cron jobs."""
        service = CronJobService()
        cron_jobs = await service.get_all_cron_jobs()

        assert isinstance(cron_jobs, list)
        assert len(cron_jobs) > 0

        for job in cron_jobs:
            assert "function_name" in job
            assert "cron_expression" in job
            assert "next_run" in job
            assert "stats" in job
            assert "schedule_description" in job

    async def test_get_cron_job_existing(self) -> None:
        """Test getting a specific existing cron job."""
        service = CronJobService()
        cron_jobs = await service.get_all_cron_jobs()

        if cron_jobs:
            function_name = cron_jobs[0]["function_name"]
            job = await service.get_cron_job(function_name)

            assert job is not None
            assert job["function_name"] == function_name
            assert "cron_expression" in job
            assert "stats" in job

    async def test_get_cron_job_nonexistent(self) -> None:
        """Test getting a nonexistent cron job returns None."""
        service = CronJobService()
        job = await service.get_cron_job("nonexistent_function_xyz")
        assert job is None

    async def test_get_summary_stats(self) -> None:
        """Test getting summary statistics."""
        service = CronJobService()
        summary = await service.get_summary_stats()

        assert isinstance(summary, dict)
        assert "total_cron_jobs" in summary
        assert "total_executions" in summary
        assert "total_complete" in summary
        assert "total_failed" in summary
        assert "overall_success_rate" in summary
        assert summary["total_cron_jobs"] > 0

    async def test_function_stats_without_redis(self) -> None:
        """Test function stats returns defaults without Redis."""
        service = CronJobService(redis=None)
        stats = await service._get_function_stats("some_function")

        assert stats["complete"] == 0
        assert stats["failed"] == 0
        assert stats["retried"] == 0
        assert stats["success_rate"] == 0.0

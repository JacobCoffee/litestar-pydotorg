"""Unit tests for job-related background tasks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from pydotorg.domains.jobs.models import Job, JobStatus


@pytest.fixture
def mock_job_ctx(mock_session_maker: AsyncMock) -> dict:
    """Mock SAQ context for job tasks."""
    return {"session_maker": mock_session_maker}


@pytest.mark.unit
class TestExpireJobs:
    """Test suite for expire_jobs task."""

    async def test_marks_expired_jobs(self, mock_job_ctx: dict, mock_session_maker: AsyncMock) -> None:
        """Test that expired jobs are marked as EXPIRED."""
        expired_job1 = Job(
            id=uuid4(),
            job_title="Expired Job 1",
            company_name="Company A",
            description="Description",
            status=JobStatus.APPROVED,
        )
        expired_job2 = Job(
            id=uuid4(),
            job_title="Expired Job 2",
            company_name="Company B",
            description="Description",
            status=JobStatus.APPROVED,
        )

        with patch("pydotorg.tasks.jobs.JobService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.mark_expired_jobs = AsyncMock(return_value=[expired_job1, expired_job2])

            from pydotorg.tasks.jobs import expire_jobs

            result = await expire_jobs(mock_job_ctx)

            assert result["count"] == 2
            mock_service.mark_expired_jobs.assert_called_once()

    async def test_handles_no_expired_jobs(self, mock_job_ctx: dict, mock_session_maker: AsyncMock) -> None:
        """Test handling when no jobs are expired."""
        with patch("pydotorg.tasks.jobs.JobService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.mark_expired_jobs = AsyncMock(return_value=[])

            from pydotorg.tasks.jobs import expire_jobs

            result = await expire_jobs(mock_job_ctx)

            assert result["count"] == 0

    async def test_raises_on_service_failure(self, mock_job_ctx: dict, mock_session_maker: AsyncMock) -> None:
        """Test that service failures are raised."""
        with patch("pydotorg.tasks.jobs.JobService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.mark_expired_jobs = AsyncMock(side_effect=Exception("DB error"))

            from pydotorg.tasks.jobs import expire_jobs

            with pytest.raises(Exception, match="DB error"):
                await expire_jobs(mock_job_ctx)


@pytest.mark.unit
class TestArchiveOldJobs:
    """Test suite for archive_old_jobs task."""

    async def test_archives_old_expired_and_rejected_jobs(
        self, mock_job_ctx: dict, mock_session_maker: AsyncMock, sample_jobs: list[Job]
    ) -> None:
        """Test archiving jobs older than threshold."""
        now = datetime.now(UTC)
        old_job = Job(
            id=uuid4(),
            job_title="Old Job",
            company_name="Company",
            description="Desc",
            status=JobStatus.EXPIRED,
            created_at=now - timedelta(days=100),
            updated_at=now - timedelta(days=100),
        )

        with patch("pydotorg.tasks.jobs.JobService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.list_by_status = AsyncMock(
                side_effect=lambda status, limit: {
                    JobStatus.EXPIRED: [old_job],
                    JobStatus.REJECTED: [],
                }[status]
            )
            mock_service.archive_job = AsyncMock()

            from pydotorg.tasks.jobs import archive_old_jobs

            result = await archive_old_jobs(mock_job_ctx, days_old=90)

            assert result["count"] == 1
            mock_service.archive_job.assert_called_once_with(old_job.id)

    async def test_uses_default_days_old(self, mock_job_ctx: dict, mock_session_maker: AsyncMock) -> None:
        """Test that default days_old is used."""
        with patch("pydotorg.tasks.jobs.JobService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.list_by_status = AsyncMock(return_value=[])

            from pydotorg.tasks.jobs import archive_old_jobs

            result = await archive_old_jobs(mock_job_ctx)

            assert result["count"] == 0
            assert mock_service.list_by_status.call_count == 2

    async def test_respects_cutoff_date(self, mock_job_ctx: dict, mock_session_maker: AsyncMock) -> None:
        """Test that cutoff date filters correctly."""
        now = datetime.now(UTC)
        old_job = Job(
            id=uuid4(),
            job_title="Old Job",
            company_name="Company",
            description="Desc",
            status=JobStatus.EXPIRED,
            created_at=now - timedelta(days=100),
            updated_at=now - timedelta(days=95),
        )
        recent_job = Job(
            id=uuid4(),
            job_title="Recent Job",
            company_name="Company",
            description="Desc",
            status=JobStatus.EXPIRED,
            created_at=now - timedelta(days=50),
            updated_at=now - timedelta(days=10),
        )

        with patch("pydotorg.tasks.jobs.JobService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.list_by_status = AsyncMock(
                side_effect=lambda status, limit: [old_job, recent_job] if status == JobStatus.EXPIRED else []
            )
            mock_service.archive_job = AsyncMock()

            from pydotorg.tasks.jobs import archive_old_jobs

            result = await archive_old_jobs(mock_job_ctx, days_old=90)

            assert result["count"] == 1
            mock_service.archive_job.assert_called_once_with(old_job.id)


@pytest.mark.unit
class TestCleanupDraftJobs:
    """Test suite for cleanup_draft_jobs task."""

    async def test_cleans_old_draft_jobs(self, mock_job_ctx: dict, mock_session_maker: AsyncMock) -> None:
        """Test that old draft jobs are archived."""
        now = datetime.now(UTC)
        old_draft = Job(
            id=uuid4(),
            job_title="Old Draft",
            company_name="Company",
            description="Desc",
            status=JobStatus.DRAFT,
            created_at=now - timedelta(days=45),
            updated_at=now - timedelta(days=45),
        )

        with patch("pydotorg.tasks.jobs.JobService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.list_by_status = AsyncMock(return_value=[old_draft])
            mock_service.archive_job = AsyncMock()

            from pydotorg.tasks.jobs import cleanup_draft_jobs

            result = await cleanup_draft_jobs(mock_job_ctx, days_old=30)

            assert result["count"] == 1
            mock_service.archive_job.assert_called_once_with(old_draft.id)

    async def test_uses_default_days_old(self, mock_job_ctx: dict, mock_session_maker: AsyncMock) -> None:
        """Test default days_old parameter."""
        with patch("pydotorg.tasks.jobs.JobService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.list_by_status = AsyncMock(return_value=[])

            from pydotorg.tasks.jobs import cleanup_draft_jobs

            result = await cleanup_draft_jobs(mock_job_ctx)

            assert result["count"] == 0
            mock_service.list_by_status.assert_called_once_with(JobStatus.DRAFT, limit=1000)

    async def test_only_affects_draft_status(self, mock_job_ctx: dict, mock_session_maker: AsyncMock) -> None:
        """Test that only DRAFT status jobs are affected."""
        with patch("pydotorg.tasks.jobs.JobService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.list_by_status = AsyncMock(return_value=[])

            from pydotorg.tasks.jobs import cleanup_draft_jobs

            await cleanup_draft_jobs(mock_job_ctx)

            call_args = mock_service.list_by_status.call_args
            assert call_args[0][0] == JobStatus.DRAFT


@pytest.mark.unit
class TestCronJobs:
    """Test suite for cron job configurations."""

    def test_cron_expire_jobs_exists(self) -> None:
        """Test that cron_expire_jobs is configured."""
        from pydotorg.tasks.jobs import cron_expire_jobs, expire_jobs

        assert cron_expire_jobs is not None
        assert cron_expire_jobs.function == expire_jobs
        assert cron_expire_jobs.cron == "0 0 * * *"

    def test_cron_archive_old_jobs_exists(self) -> None:
        """Test that cron_archive_old_jobs is configured."""
        from pydotorg.tasks.jobs import archive_old_jobs, cron_archive_old_jobs

        assert cron_archive_old_jobs is not None
        assert cron_archive_old_jobs.function == archive_old_jobs
        assert cron_archive_old_jobs.kwargs["days_old"] == 90
        assert cron_archive_old_jobs.cron == "0 0 * * 0"

    def test_cron_cleanup_draft_jobs_exists(self) -> None:
        """Test that cron_cleanup_draft_jobs is configured."""
        from pydotorg.tasks.jobs import cleanup_draft_jobs, cron_cleanup_draft_jobs

        assert cron_cleanup_draft_jobs is not None
        assert cron_cleanup_draft_jobs.function == cleanup_draft_jobs
        assert cron_cleanup_draft_jobs.kwargs["days_old"] == 30
        assert cron_cleanup_draft_jobs.cron == "0 0 1 * *"

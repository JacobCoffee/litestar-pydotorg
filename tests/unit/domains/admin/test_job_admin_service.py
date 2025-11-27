"""Unit tests for JobAdminService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest

from pydotorg.domains.admin.services.jobs import JobAdminService
from pydotorg.domains.jobs.models import Job, JobStatus


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock async session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_creator() -> Mock:
    """Create a mock user for job creator."""
    creator = Mock()
    creator.id = uuid4()
    creator.email = "creator@example.com"
    creator.username = "jobcreator"
    return creator


@pytest.fixture
def mock_job(mock_creator: Mock) -> Mock:
    """Create a mock job."""
    job = Mock(spec=Job)
    job.id = uuid4()
    job.job_title = "Python Developer"
    job.company_name = "Test Company"
    job.description = "A great job opportunity"
    job.status = JobStatus.REVIEW
    job.city = "San Francisco"
    job.country = "USA"
    job.telecommuting = True
    job.contact_email = "jobs@example.com"
    job.slug = "python-developer-test-company"
    job.created_at = None
    job.creator = mock_creator
    job.category = None
    job.job_types = []
    job.review_comments = []
    return job


@pytest.fixture
def service(mock_session: AsyncMock) -> JobAdminService:
    """Create a JobAdminService instance with mock session."""
    return JobAdminService(session=mock_session)


class TestListJobs:
    """Tests for JobAdminService.list_jobs."""

    async def test_list_jobs_returns_jobs_and_count(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
        mock_job: Mock,
    ) -> None:
        """Test that list_jobs returns jobs and total count."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_jobs_result = MagicMock()
        mock_jobs_result.scalars.return_value.all.return_value = [mock_job]

        mock_session.execute.side_effect = [mock_count_result, mock_jobs_result]

        jobs, total = await service.list_jobs()

        assert total == 1
        assert len(jobs) == 1
        assert jobs[0] == mock_job

    async def test_list_jobs_with_status_filter(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
        mock_job: Mock,
    ) -> None:
        """Test list_jobs with status filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_jobs_result = MagicMock()
        mock_jobs_result.scalars.return_value.all.return_value = [mock_job]

        mock_session.execute.side_effect = [mock_count_result, mock_jobs_result]

        _jobs, total = await service.list_jobs(status="review")

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_jobs_with_search(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
        mock_job: Mock,
    ) -> None:
        """Test list_jobs with search filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_jobs_result = MagicMock()
        mock_jobs_result.scalars.return_value.all.return_value = [mock_job]

        mock_session.execute.side_effect = [mock_count_result, mock_jobs_result]

        _jobs, total = await service.list_jobs(search="Python")

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_jobs_with_pagination(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
        mock_job: Mock,
    ) -> None:
        """Test list_jobs with pagination."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100

        mock_jobs_result = MagicMock()
        mock_jobs_result.scalars.return_value.all.return_value = [mock_job]

        mock_session.execute.side_effect = [mock_count_result, mock_jobs_result]

        jobs, total = await service.list_jobs(limit=10, offset=20)

        assert total == 100
        assert len(jobs) == 1

    async def test_list_jobs_empty_result(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test list_jobs with no results."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_jobs_result = MagicMock()
        mock_jobs_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_jobs_result]

        jobs, total = await service.list_jobs()

        assert total == 0
        assert len(jobs) == 0


class TestGetJob:
    """Tests for JobAdminService.get_job."""

    async def test_get_job_found(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
        mock_job: Mock,
    ) -> None:
        """Test get_job returns job when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        job = await service.get_job(mock_job.id)

        assert job == mock_job

    async def test_get_job_not_found(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_job returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        job = await service.get_job(uuid4())

        assert job is None


class TestApproveJob:
    """Tests for JobAdminService.approve_job."""

    async def test_approve_job_success(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
        mock_job: Mock,
    ) -> None:
        """Test approving an existing job."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        job = await service.approve_job(mock_job.id)

        assert job.status == JobStatus.APPROVED
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_job)

    async def test_approve_job_not_found(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test approving non-existent job returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        job = await service.approve_job(uuid4())

        assert job is None
        mock_session.commit.assert_not_called()


class TestRejectJob:
    """Tests for JobAdminService.reject_job."""

    async def test_reject_job_success(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
        mock_job: Mock,
    ) -> None:
        """Test rejecting an existing job."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        job = await service.reject_job(mock_job.id)

        assert job.status == JobStatus.REJECTED
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_job)

    async def test_reject_job_not_found(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test rejecting non-existent job returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        job = await service.reject_job(uuid4())

        assert job is None
        mock_session.commit.assert_not_called()


class TestAddReviewComment:
    """Tests for JobAdminService.add_review_comment."""

    async def test_add_review_comment_success(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
        mock_job: Mock,
    ) -> None:
        """Test adding review comment to job."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        reviewer_id = uuid4()
        comment = await service.add_review_comment(
            job_id=mock_job.id,
            comment="This looks good!",
            reviewer_id=reviewer_id,
        )

        assert comment is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called()

    async def test_add_review_comment_job_not_found(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test adding comment to non-existent job returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        comment = await service.add_review_comment(
            job_id=uuid4(),
            comment="Test comment",
            reviewer_id=uuid4(),
        )

        assert comment is None
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


class TestGetStats:
    """Tests for JobAdminService.get_stats."""

    async def test_get_stats_returns_all_counts(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_stats returns all job statistics."""
        mock_total = MagicMock()
        mock_total.scalar.return_value = 100

        mock_pending = MagicMock()
        mock_pending.scalar.return_value = 25

        mock_approved = MagicMock()
        mock_approved.scalar.return_value = 60

        mock_rejected = MagicMock()
        mock_rejected.scalar.return_value = 15

        mock_session.execute.side_effect = [
            mock_total,
            mock_pending,
            mock_approved,
            mock_rejected,
        ]

        stats = await service.get_stats()

        assert stats["total_jobs"] == 100
        assert stats["pending_jobs"] == 25
        assert stats["approved_jobs"] == 60
        assert stats["rejected_jobs"] == 15
        assert mock_session.execute.call_count == 4

    async def test_get_stats_empty_database(
        self,
        service: JobAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_stats with no jobs."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0

        mock_session.execute.return_value = mock_result

        stats = await service.get_stats()

        assert stats["total_jobs"] == 0
        assert stats["pending_jobs"] == 0
        assert stats["approved_jobs"] == 0
        assert stats["rejected_jobs"] == 0

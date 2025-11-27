"""Unit tests for search indexing background tasks."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from pydotorg.domains.jobs.models import Job, JobStatus


@pytest.fixture
def mock_search_service() -> MagicMock:
    """Mock SearchService for testing."""
    service = MagicMock()
    service.clear_index = AsyncMock()
    service.index_documents = AsyncMock(return_value=MagicMock(task_uid=123))
    service.update_documents = AsyncMock(return_value=MagicMock(task_uid=124))
    service.delete_documents = AsyncMock(return_value=MagicMock(task_uid=125))
    service.create_index = AsyncMock()
    service.configure_index = AsyncMock()
    service.close = AsyncMock()
    return service


@pytest.fixture
def search_ctx(mock_session_maker: AsyncMock) -> dict:
    """Mock SAQ context for search tasks."""
    return {"session_maker": mock_session_maker}


@pytest.mark.unit
class TestIndexAllJobs:
    """Test suite for index_all_jobs task."""

    async def test_indexes_all_approved_jobs(
        self, search_ctx: dict, mock_session_maker: AsyncMock, mock_search_service: MagicMock, sample_jobs: list[Job]
    ) -> None:
        """Test that all approved jobs are indexed."""
        session = mock_session_maker.return_value.__aenter__.return_value
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            j for j in sample_jobs if j.status == JobStatus.APPROVED
        ] or sample_jobs[:1]
        session.execute = AsyncMock(return_value=mock_result)

        with patch("pydotorg.tasks.search._get_search_service", return_value=mock_search_service):
            from pydotorg.tasks.search import index_all_jobs

            result = await index_all_jobs(search_ctx)

            assert "indexed" in result
            assert "duration_seconds" in result

    async def test_handles_empty_job_list(
        self, search_ctx: dict, mock_session_maker: AsyncMock, mock_search_service: MagicMock
    ) -> None:
        """Test handling when no jobs exist."""
        session = mock_session_maker.return_value.__aenter__.return_value
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with patch("pydotorg.tasks.search._get_search_service", return_value=mock_search_service):
            from pydotorg.tasks.search import index_all_jobs

            result = await index_all_jobs(search_ctx)

            assert result["indexed"] == 0


@pytest.mark.unit
class TestIndexJob:
    """Test suite for index_job task."""

    async def test_indexes_single_job_by_id(
        self, search_ctx: dict, mock_session_maker: AsyncMock, mock_search_service: MagicMock, sample_job: Job
    ) -> None:
        """Test indexing a single job by ID."""
        session = mock_session_maker.return_value.__aenter__.return_value
        mock_result = MagicMock()
        sample_job.status = JobStatus.APPROVED
        mock_result.scalar_one_or_none.return_value = sample_job
        session.execute = AsyncMock(return_value=mock_result)

        with patch("pydotorg.tasks.search._get_search_service", return_value=mock_search_service):
            from pydotorg.tasks.search import index_job

            result = await index_job(search_ctx, job_id=str(sample_job.id))

            assert result["indexed"] == 1
            mock_search_service.update_documents.assert_called_once()

    async def test_handles_nonexistent_job(
        self, search_ctx: dict, mock_session_maker: AsyncMock, mock_search_service: MagicMock
    ) -> None:
        """Test handling of nonexistent job ID."""
        job_id = uuid4()
        session = mock_session_maker.return_value.__aenter__.return_value
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        with patch("pydotorg.tasks.search._get_search_service", return_value=mock_search_service):
            from pydotorg.tasks.search import index_job

            result = await index_job(search_ctx, job_id=str(job_id))

            assert result["indexed"] == 0
            assert result["reason"] == "not_found"

    async def test_removes_non_approved_jobs_from_index(
        self, search_ctx: dict, mock_session_maker: AsyncMock, mock_search_service: MagicMock, sample_job: Job
    ) -> None:
        """Test that non-approved jobs are removed from index."""
        sample_job.status = JobStatus.DRAFT
        session = mock_session_maker.return_value.__aenter__.return_value
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_job
        session.execute = AsyncMock(return_value=mock_result)

        with patch("pydotorg.tasks.search._get_search_service", return_value=mock_search_service):
            from pydotorg.tasks.search import index_job

            result = await index_job(search_ctx, job_id=str(sample_job.id))

            assert result["indexed"] == 0
            assert result["action"] == "removed"
            mock_search_service.delete_documents.assert_called_once()


@pytest.mark.unit
class TestRemoveJobFromIndex:
    """Test suite for remove_job_from_index task."""

    async def test_removes_job_from_index(self, search_ctx: dict, mock_search_service: MagicMock) -> None:
        """Test removal of job from search index."""
        job_id = str(uuid4())

        with patch("pydotorg.tasks.search._get_search_service", return_value=mock_search_service):
            from pydotorg.tasks.search import remove_job_from_index

            result = await remove_job_from_index(search_ctx, job_id=job_id)

            assert result["removed"] == 1
            assert result["job_id"] == job_id
            mock_search_service.delete_documents.assert_called_once()


@pytest.mark.unit
class TestRebuildSearchIndex:
    """Test suite for rebuild_search_index task."""

    async def test_rebuilds_all_indexes(
        self, search_ctx: dict, mock_session_maker: AsyncMock, mock_search_service: MagicMock
    ) -> None:
        """Test that all indexes are rebuilt."""
        session = mock_session_maker.return_value.__aenter__.return_value
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with patch("pydotorg.tasks.search._get_search_service", return_value=mock_search_service):
            from pydotorg.tasks.search import rebuild_search_index

            result = await rebuild_search_index(search_ctx)

            assert "total_indexed" in result
            assert "duration_seconds" in result
            assert "results" in result
            assert mock_search_service.create_index.called
            assert mock_search_service.configure_index.called

    async def test_configures_all_index_types(
        self, search_ctx: dict, mock_session_maker: AsyncMock, mock_search_service: MagicMock
    ) -> None:
        """Test that all index types are configured."""
        session = mock_session_maker.return_value.__aenter__.return_value
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with patch("pydotorg.tasks.search._get_search_service", return_value=mock_search_service):
            from pydotorg.tasks.search import rebuild_search_index

            result = await rebuild_search_index(search_ctx)

            assert "jobs" in result["results"]
            assert "events" in result["results"]
            assert "pages" in result["results"]
            assert "blogs" in result["results"]


@pytest.mark.unit
class TestIndexContent:
    """Test suite for index_content task."""

    async def test_indexes_job_content(
        self, search_ctx: dict, mock_session_maker: AsyncMock, mock_search_service: MagicMock, sample_job: Job
    ) -> None:
        """Test indexing job content type."""
        sample_job.status = JobStatus.APPROVED
        session = mock_session_maker.return_value.__aenter__.return_value
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_job
        session.execute = AsyncMock(return_value=mock_result)

        with patch("pydotorg.tasks.search._get_search_service", return_value=mock_search_service):
            from pydotorg.tasks.search import index_content

            result = await index_content(search_ctx, content_type="job", content_id=str(sample_job.id))

            assert result["success"] is True

    async def test_handles_unknown_content_type(self, search_ctx: dict) -> None:
        """Test handling of unknown content type."""
        from pydotorg.tasks.search import index_content

        result = await index_content(search_ctx, content_type="unknown", content_id=str(uuid4()))

        assert result["success"] is False
        assert "error" in result


@pytest.mark.unit
class TestIndexAllEvents:
    """Test suite for index_all_events task."""

    async def test_indexes_published_events(
        self, search_ctx: dict, mock_session_maker: AsyncMock, mock_search_service: MagicMock
    ) -> None:
        """Test that published events are indexed."""
        session = mock_session_maker.return_value.__aenter__.return_value
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with patch("pydotorg.tasks.search._get_search_service", return_value=mock_search_service):
            from pydotorg.tasks.search import index_all_events

            result = await index_all_events(search_ctx)

            assert "indexed" in result
            assert "duration_seconds" in result


@pytest.mark.unit
class TestIndexAllPages:
    """Test suite for index_all_pages task."""

    async def test_indexes_published_pages(
        self, search_ctx: dict, mock_session_maker: AsyncMock, mock_search_service: MagicMock
    ) -> None:
        """Test that published pages are indexed."""
        session = mock_session_maker.return_value.__aenter__.return_value
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with patch("pydotorg.tasks.search._get_search_service", return_value=mock_search_service):
            from pydotorg.tasks.search import index_all_pages

            result = await index_all_pages(search_ctx)

            assert "indexed" in result
            assert "duration_seconds" in result


@pytest.mark.unit
class TestIndexAllBlogs:
    """Test suite for index_all_blogs task."""

    async def test_indexes_blog_entries(
        self, search_ctx: dict, mock_session_maker: AsyncMock, mock_search_service: MagicMock
    ) -> None:
        """Test that blog entries are indexed."""
        session = mock_session_maker.return_value.__aenter__.return_value
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with patch("pydotorg.tasks.search._get_search_service", return_value=mock_search_service):
            from pydotorg.tasks.search import index_all_blogs

            result = await index_all_blogs(search_ctx)

            assert "indexed" in result
            assert "duration_seconds" in result


@pytest.mark.unit
class TestCronRebuildIndexes:
    """Test suite for cron_rebuild_indexes configuration."""

    def test_cron_rebuild_indexes_exists(self) -> None:
        """Test that cron_rebuild_indexes is configured."""
        from pydotorg.tasks.search import cron_rebuild_indexes, rebuild_search_index

        assert cron_rebuild_indexes is not None
        assert cron_rebuild_indexes.function == rebuild_search_index
        assert cron_rebuild_indexes.cron == "0 3 * * 0"

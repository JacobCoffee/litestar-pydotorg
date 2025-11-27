"""Unit tests for SAQ worker configuration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.unit
class TestWorkerSettings:
    """Test suite for worker settings configuration."""

    def test_saq_settings_structure(self) -> None:
        """Test that saq_settings has correct structure."""
        from pydotorg.tasks.worker import saq_settings

        assert "queue" in saq_settings
        assert "functions" in saq_settings
        assert "concurrency" in saq_settings
        assert "cron_jobs" in saq_settings
        assert "startup" in saq_settings
        assert "shutdown" in saq_settings

    def test_worker_has_required_concurrency(self) -> None:
        """Test that worker has appropriate concurrency settings."""
        from pydotorg.tasks.worker import saq_settings

        assert saq_settings["concurrency"] > 0
        assert saq_settings["concurrency"] <= 20

    def test_worker_uses_redis_queue(self) -> None:
        """Test that worker uses Redis for queue."""
        from pydotorg.tasks.worker import queue

        assert queue is not None

    def test_get_task_functions_returns_callable_list(self) -> None:
        """Test that get_task_functions returns list of callables."""
        from pydotorg.tasks.worker import get_task_functions

        functions = get_task_functions()

        assert isinstance(functions, list)
        assert len(functions) > 0
        for func in functions:
            assert callable(func)

    def test_worker_functions_registered(self) -> None:
        """Test that all task functions are registered."""
        from pydotorg.tasks.worker import get_task_functions

        functions = get_task_functions()
        function_names = [func.__name__ for func in functions]

        expected_functions = [
            "refresh_all_feeds",
            "refresh_stale_feeds",
            "refresh_single_feed",
            "expire_jobs",
            "archive_old_jobs",
            "cleanup_draft_jobs",
            "send_verification_email",
            "send_password_reset_email",
            "send_job_approved_email",
            "index_all_jobs",
            "index_job",
            "rebuild_search_index",
            "warm_homepage_cache",
            "clear_cache",
        ]

        for func_name in expected_functions:
            assert func_name in function_names, f"Expected function {func_name} not found"


@pytest.mark.unit
class TestCronJobConfiguration:
    """Test suite for cron job configuration."""

    def test_get_cron_jobs_returns_list(self) -> None:
        """Test that get_cron_jobs returns list of CronJob objects."""
        from pydotorg.tasks.worker import get_cron_jobs

        cron_jobs = get_cron_jobs()

        assert isinstance(cron_jobs, list)
        assert len(cron_jobs) > 0

    def test_feed_refresh_cron_configured(self) -> None:
        """Test that feed refresh cron job is configured."""
        from pydotorg.tasks.feeds import cron_refresh_feeds

        assert cron_refresh_feeds is not None
        assert hasattr(cron_refresh_feeds, "cron")

    def test_job_expiration_cron_configured(self) -> None:
        """Test that job expiration cron job is configured."""
        from pydotorg.tasks.jobs import cron_expire_jobs

        assert cron_expire_jobs is not None
        assert hasattr(cron_expire_jobs, "cron")

    def test_cache_warming_cron_configured(self) -> None:
        """Test that cache warming cron job is configured."""
        from pydotorg.tasks.cache import cron_warm_homepage_cache

        assert cron_warm_homepage_cache is not None
        assert hasattr(cron_warm_homepage_cache, "cron")

    def test_search_indexing_cron_configured(self) -> None:
        """Test that search indexing cron job is configured."""
        from pydotorg.tasks.search import cron_rebuild_indexes

        assert cron_rebuild_indexes is not None
        assert hasattr(cron_rebuild_indexes, "cron")


@pytest.mark.unit
class TestWorkerStartupShutdown:
    """Test suite for worker startup and shutdown hooks."""

    async def test_startup_initializes_resources(self) -> None:
        """Test that startup initializes required resources."""
        from pydotorg.tasks.worker import startup

        ctx: dict = {}

        with (
            patch("pydotorg.tasks.worker.SQLAlchemyAsyncConfig") as mock_config,
            patch("redis.asyncio.Redis") as mock_redis_class,
        ):
            mock_engine = MagicMock()
            mock_session_maker = MagicMock()
            mock_config.return_value.get_engine.return_value = mock_engine
            mock_config.return_value.create_session_maker.return_value = mock_session_maker

            mock_redis = AsyncMock()
            mock_redis_class.from_url.return_value = mock_redis

            await startup(ctx)

            assert "engine" in ctx
            assert "session_maker" in ctx
            assert "redis" in ctx

    async def test_shutdown_closes_connections(self) -> None:
        """Test that shutdown closes service connections."""
        from pydotorg.tasks.worker import shutdown

        mock_engine = AsyncMock()
        mock_redis = AsyncMock()

        ctx = {
            "engine": mock_engine,
            "redis": mock_redis,
        }

        await shutdown(ctx)

        mock_engine.dispose.assert_called_once()
        mock_redis.aclose.assert_called_once()

    async def test_shutdown_handles_missing_resources(self) -> None:
        """Test that shutdown handles missing resources gracefully."""
        from pydotorg.tasks.worker import shutdown

        ctx: dict = {}

        await shutdown(ctx)


@pytest.mark.unit
class TestBeforeAfterProcessHooks:
    """Test suite for before/after process hooks."""

    async def test_before_process_logs_job_info(self) -> None:
        """Test that before_process logs job info."""
        from pydotorg.tasks.worker import before_process

        mock_job = MagicMock()
        mock_job.function = "test_task"
        mock_job.key = "test-key-123"
        mock_job.attempts = 1

        ctx = {"job": mock_job}

        await before_process(ctx)

    async def test_after_process_logs_completion(self) -> None:
        """Test that after_process logs task completion."""
        from pydotorg.tasks.worker import after_process

        mock_job = MagicMock()
        mock_job.function = "test_task"
        mock_job.key = "test-key-123"

        ctx = {"job": mock_job}

        await after_process(ctx)

    async def test_before_process_handles_missing_job(self) -> None:
        """Test that before_process handles missing job gracefully."""
        from pydotorg.tasks.worker import before_process

        ctx: dict = {}

        await before_process(ctx)

    async def test_after_process_handles_missing_job(self) -> None:
        """Test that after_process handles missing job gracefully."""
        from pydotorg.tasks.worker import after_process

        ctx: dict = {}

        await after_process(ctx)

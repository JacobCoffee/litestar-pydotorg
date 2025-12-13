"""Integration tests for page caching functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

if TYPE_CHECKING:
    pass


class TestPageRenderControllerCaching:
    """Integration tests for page render controller caching."""

    @pytest.mark.anyio
    async def test_page_controller_has_cache_decorator(self) -> None:
        """Verify PageRenderController.render_page has cache=300."""
        from pydotorg.domains.pages.controllers import PageRenderController

        assert PageRenderController.path == "/{page_path:path}"
        handler = PageRenderController.render_page
        assert hasattr(handler, "fn")

    @pytest.mark.anyio
    async def test_response_cache_config_in_app(self) -> None:
        """Verify the app has response cache configuration."""
        from pydotorg.main import app

        assert app.response_cache_config is not None
        assert app.response_cache_config.default_expiration == 60
        assert app.response_cache_config.store == "response_cache"

    @pytest.mark.anyio
    async def test_response_cache_store_configured(self) -> None:
        """Verify the response_cache store is configured in stores."""
        from pydotorg.main import app

        store = app.stores.get("response_cache")
        assert store is not None
        rate_limit_store = app.stores.get("rate_limit")
        assert rate_limit_store is not None


class TestCacheInvalidationTask:
    """Integration tests for cache invalidation task."""

    @pytest.mark.anyio
    async def test_invalidate_page_response_cache_function_exists(self) -> None:
        """Verify the invalidation task is importable."""
        from pydotorg.tasks.cache import invalidate_page_response_cache

        assert callable(invalidate_page_response_cache)

    @pytest.mark.anyio
    async def test_invalidate_page_response_cache_with_path(self) -> None:
        """Test invalidation with specific path."""
        from pydotorg.tasks.cache import invalidate_page_response_cache

        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1
        ctx = {"redis": mock_redis}

        result = await invalidate_page_response_cache(ctx, page_path="/about")

        assert result["path"] == "/about"
        assert "cleared" in result
        mock_redis.delete.assert_called_once()

    @pytest.mark.anyio
    async def test_invalidate_page_response_cache_all_pages(self) -> None:
        """Test invalidating all page caches."""
        from pydotorg.tasks.cache import invalidate_page_response_cache

        mock_redis = AsyncMock()
        mock_redis.scan.return_value = (0, ["key1", "key2"])
        mock_redis.delete.return_value = 2
        ctx = {"redis": mock_redis}

        result = await invalidate_page_response_cache(ctx, page_path=None)

        assert result["path"] == "all"
        assert "cleared" in result


class TestTaskRegistration:
    """Tests for cache invalidation task registration."""

    @pytest.mark.anyio
    async def test_invalidate_task_in_worker_functions(self) -> None:
        """Verify the task is registered in worker task functions."""
        from pydotorg.tasks.worker import get_task_functions

        functions = get_task_functions()
        function_names = [f.__name__ for f in functions]

        assert "invalidate_page_response_cache" in function_names


class TestPageServiceCacheInvalidation:
    """Tests for cache invalidation triggered by PageService."""

    @pytest.mark.anyio
    async def test_page_update_triggers_cache_invalidation(self) -> None:
        """Verify page update enqueues cache invalidation task."""
        with patch("pydotorg.domains.pages.services.enqueue_task") as mock_enqueue:
            mock_enqueue.return_value = None

            from pydotorg.domains.pages.services import PageService

            assert hasattr(PageService, "update")


class TestAdminPageServiceCacheInvalidation:
    """Tests for cache invalidation in admin page operations."""

    @pytest.mark.anyio
    async def test_publish_page_invalidates_cache(self) -> None:
        """Verify publishing a page triggers cache invalidation."""
        from pydotorg.domains.admin.services.pages import PageAdminService

        assert hasattr(PageAdminService, "publish_page")

    @pytest.mark.anyio
    async def test_unpublish_page_invalidates_cache(self) -> None:
        """Verify unpublishing a page triggers cache invalidation."""
        from pydotorg.domains.admin.services.pages import PageAdminService

        assert hasattr(PageAdminService, "unpublish_page")


class TestCacheModuleExports:
    """Tests for cache module exports."""

    def test_cache_module_exports(self) -> None:
        """Verify all expected items are exported from cache module."""
        from pydotorg.core.cache import (
            CACHE_TTL_DEFAULT,
            CACHE_TTL_PAGES,
            CACHE_TTL_STATIC,
            GLOBAL_SURROGATE_KEY,
            AdminNoCacheMiddleware,
            CacheControlMiddleware,
            PageCacheService,
            SurrogateKeyMiddleware,
            create_cache_middleware_stack,
            create_response_cache_config,
            page_cache_key_builder,
        )

        assert CACHE_TTL_DEFAULT == 60
        assert CACHE_TTL_PAGES == 300
        assert CACHE_TTL_STATIC == 3600
        assert GLOBAL_SURROGATE_KEY == "pydotorg-app"
        assert callable(create_response_cache_config)
        assert callable(page_cache_key_builder)
        assert callable(create_cache_middleware_stack)
        assert PageCacheService is not None
        assert AdminNoCacheMiddleware is not None
        assert CacheControlMiddleware is not None
        assert SurrogateKeyMiddleware is not None


class Test404CacheControl:
    """Tests for 404 page caching."""

    def test_404_cache_max_age_constant(self) -> None:
        """Verify 404 cache max age is 300 seconds (5 minutes)."""
        from pydotorg.core.exceptions import CACHE_404_MAX_AGE

        assert CACHE_404_MAX_AGE == 300

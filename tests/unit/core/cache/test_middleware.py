"""Unit tests for cache control middleware."""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Litestar, get
from litestar.testing import TestClient

if TYPE_CHECKING:
    pass


class TestAdminNoCacheMiddleware:
    """Tests for AdminNoCacheMiddleware."""

    def test_admin_path_has_private_cache_control(self) -> None:
        """Admin paths should have Cache-Control: private, no-store."""
        from pydotorg.core.cache.middleware import AdminNoCacheMiddleware

        @get("/admin/dashboard")
        async def admin_handler() -> dict:
            return {"status": "ok"}

        app = Litestar(
            route_handlers=[admin_handler],
            middleware=[AdminNoCacheMiddleware],
        )

        with TestClient(app) as client:
            response = client.get("/admin/dashboard")
            assert response.status_code == 200
            assert response.headers.get("cache-control") == "private, no-store"

    def test_non_admin_path_no_cache_control_from_admin_middleware(self) -> None:
        """Non-admin paths should not get Cache-Control from AdminNoCacheMiddleware."""
        from pydotorg.core.cache.middleware import AdminNoCacheMiddleware

        @get("/public")
        async def public_handler() -> dict:
            return {"status": "ok"}

        app = Litestar(
            route_handlers=[public_handler],
            middleware=[AdminNoCacheMiddleware],
        )

        with TestClient(app) as client:
            response = client.get("/public")
            assert response.status_code == 200
            assert "private, no-store" not in response.headers.get("cache-control", "")


class TestCacheControlMiddleware:
    """Tests for CacheControlMiddleware."""

    def test_static_path_has_long_cache(self) -> None:
        """Static paths should have long Cache-Control max-age."""
        from pydotorg.core.cache.middleware import CacheControlMiddleware

        @get("/static/file.js")
        async def static_handler() -> dict:
            return {"content": "js"}

        app = Litestar(
            route_handlers=[static_handler],
            middleware=[CacheControlMiddleware],
        )

        with TestClient(app) as client:
            response = client.get("/static/file.js")
            assert response.status_code == 200
            cache_control = response.headers.get("cache-control", "")
            assert "public" in cache_control
            assert "max-age=31536000" in cache_control
            assert "immutable" in cache_control

    def test_api_path_has_no_store(self) -> None:
        """API paths should have Cache-Control: no-store."""
        from pydotorg.core.cache.middleware import CacheControlMiddleware

        @get("/api/v1/users")
        async def api_handler() -> dict:
            return {"users": []}

        app = Litestar(
            route_handlers=[api_handler],
            middleware=[CacheControlMiddleware],
        )

        with TestClient(app) as client:
            response = client.get("/api/v1/users")
            assert response.status_code == 200
            assert response.headers.get("cache-control") == "no-store"

    def test_page_path_has_default_cache(self) -> None:
        """Regular page paths should have default Cache-Control."""
        from pydotorg.core.cache.middleware import CacheControlMiddleware

        @get("/about")
        async def page_handler() -> dict:
            return {"title": "About"}

        app = Litestar(
            route_handlers=[page_handler],
            middleware=[CacheControlMiddleware],
        )

        with TestClient(app) as client:
            response = client.get("/about")
            assert response.status_code == 200
            cache_control = response.headers.get("cache-control", "")
            assert "public" in cache_control
            assert "max-age=300" in cache_control

    def test_admin_path_has_no_cache(self) -> None:
        """Admin paths should have private, no-store Cache-Control."""
        from pydotorg.core.cache.middleware import CacheControlMiddleware

        @get("/admin/settings")
        async def admin_handler() -> dict:
            return {"settings": {}}

        app = Litestar(
            route_handlers=[admin_handler],
            middleware=[CacheControlMiddleware],
        )

        with TestClient(app) as client:
            response = client.get("/admin/settings")
            assert response.status_code == 200
            assert response.headers.get("cache-control") == "private, no-store"

    def test_auth_path_has_no_cache(self) -> None:
        """Auth paths should have private, no-store Cache-Control."""
        from pydotorg.core.cache.middleware import CacheControlMiddleware

        @get("/auth/login")
        async def auth_handler() -> dict:
            return {"form": True}

        app = Litestar(
            route_handlers=[auth_handler],
            middleware=[CacheControlMiddleware],
        )

        with TestClient(app) as client:
            response = client.get("/auth/login")
            assert response.status_code == 200
            assert response.headers.get("cache-control") == "private, no-store"

    def test_existing_cache_control_not_overwritten(self) -> None:
        """Routes with existing Cache-Control should not be overwritten.

        When a handler sets Cache-Control explicitly, the middleware
        should not override it.
        """
        from pydotorg.core.cache.middleware import CacheControlMiddleware

        @get("/custom", response_headers={"Cache-Control": "public, max-age=600"})
        async def custom_handler() -> dict:
            return {"custom": True}

        app = Litestar(
            route_handlers=[custom_handler],
            middleware=[CacheControlMiddleware],
        )

        with TestClient(app) as client:
            response = client.get("/custom")
            assert response.status_code == 200
            cache_control = response.headers.get("cache-control", "")
            assert "600" in cache_control


class TestSurrogateKeyMiddleware:
    """Tests for SurrogateKeyMiddleware."""

    def test_adds_global_surrogate_key(self) -> None:
        """Response should have global Surrogate-Key header."""
        from pydotorg.core.cache.middleware import SurrogateKeyMiddleware

        @get("/page")
        async def page_handler() -> dict:
            return {"title": "Page"}

        app = Litestar(
            route_handlers=[page_handler],
            middleware=[SurrogateKeyMiddleware],
        )

        with TestClient(app) as client:
            response = client.get("/page")
            assert response.status_code == 200
            surrogate_key = response.headers.get("surrogate-key", "")
            assert "pydotorg-app" in surrogate_key

    def test_custom_surrogate_key(self) -> None:
        """Middleware should use custom surrogate key when provided."""
        from pydotorg.core.cache.middleware import SurrogateKeyMiddleware

        @get("/page")
        async def page_handler() -> dict:
            return {"title": "Page"}

        class CustomSurrogateKeyMiddleware(SurrogateKeyMiddleware):
            def __init__(self, app):
                super().__init__(app, surrogate_key="custom-app")

        app = Litestar(
            route_handlers=[page_handler],
            middleware=[CustomSurrogateKeyMiddleware],
        )

        with TestClient(app) as client:
            response = client.get("/page")
            assert response.status_code == 200
            surrogate_key = response.headers.get("surrogate-key", "")
            assert "custom-app" in surrogate_key


class TestCacheMiddlewareStack:
    """Tests for the combined cache middleware stack."""

    def test_create_cache_middleware_stack_returns_middleware(self) -> None:
        """create_cache_middleware_stack should return middleware list."""
        from pydotorg.core.cache.middleware import (
            AdminNoCacheMiddleware,
            CacheControlMiddleware,
            SurrogateKeyMiddleware,
            create_cache_middleware_stack,
        )

        stack = create_cache_middleware_stack(enable_surrogate_keys=True)
        assert AdminNoCacheMiddleware in stack
        assert CacheControlMiddleware in stack
        assert SurrogateKeyMiddleware in stack

    def test_create_cache_middleware_stack_without_surrogate_keys(self) -> None:
        """create_cache_middleware_stack without surrogate keys."""
        from pydotorg.core.cache.middleware import (
            AdminNoCacheMiddleware,
            CacheControlMiddleware,
            SurrogateKeyMiddleware,
            create_cache_middleware_stack,
        )

        stack = create_cache_middleware_stack(enable_surrogate_keys=False)
        assert AdminNoCacheMiddleware in stack
        assert CacheControlMiddleware in stack
        assert SurrogateKeyMiddleware not in stack


class TestCacheMiddlewareExports:
    """Tests for cache middleware module exports."""

    def test_module_exports(self) -> None:
        """Verify all expected items are exported from cache module."""
        from pydotorg.core.cache import (
            GLOBAL_SURROGATE_KEY,
            AdminNoCacheMiddleware,
            CacheControlMiddleware,
            SurrogateKeyMiddleware,
            create_cache_middleware_stack,
        )

        assert GLOBAL_SURROGATE_KEY == "pydotorg-app"
        assert AdminNoCacheMiddleware is not None
        assert CacheControlMiddleware is not None
        assert SurrogateKeyMiddleware is not None
        assert callable(create_cache_middleware_stack)

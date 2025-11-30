"""Admin settings controller for site configuration management."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from litestar import Controller, get, post
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.response import Redirect, Response, Template
from litestar.stores.redis import RedisStore

from pydotorg.core.auth.guards import require_staff
from pydotorg.domains.admin import urls
from pydotorg.lib.tasks import enqueue_task

if TYPE_CHECKING:
    from litestar import Request


def _admin_auth_exception_handler(request: Request, exc: NotAuthorizedException) -> Response:
    """Redirect to login page when user is not authenticated."""
    next_url = quote(str(request.url), safe="")
    return Redirect(f"/auth/login?next={next_url}")


def _admin_permission_exception_handler(request: Request, exc: PermissionDeniedException) -> Response:
    """Show 403 template when user lacks permissions."""
    return Template(
        template_name="errors/403.html.jinja2",
        context={
            "title": "Access Denied",
            "message": str(exc.detail) if exc.detail else "You do not have permission to access this page.",
        },
        status_code=403,
    )


class AdminSettingsController(Controller):
    """Controller for admin site settings management."""

    path = urls.ADMIN_SETTINGS
    include_in_schema = False
    guards = [require_staff]
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def settings_page(self) -> Template:
        """Render site settings page.

        Returns:
            Site settings template
        """
        return Template(
            template_name="admin/settings/index.html.jinja2",
            context={
                "title": "Site Settings",
                "description": "Manage site configuration",
            },
        )

    @get("/cache")
    async def cache_management_page(self, request: Request) -> Template:
        """Render cache management page with live stats.

        Returns:
            Cache management template with Redis stats
        """
        cache_stats = await self._get_cache_stats(request)
        return Template(
            template_name="admin/settings/cache.html.jinja2",
            context={
                "title": "Cache Management",
                "description": "View cache statistics and clear cached data",
                "stats": cache_stats,
            },
        )

    @post("/cache/clear-pages")
    async def clear_page_cache(self, request: Request) -> Redirect:
        """Clear all page response caches.

        Returns:
            Redirect back to cache management page
        """
        await enqueue_task("invalidate_page_response_cache", page_path=None)
        request.app.state.setdefault("flash_messages", []).append(
            {
                "type": "success",
                "message": "Page cache clear task queued successfully.",
            }
        )
        return Redirect("/admin/settings/cache")

    @post("/cache/clear-all")
    async def clear_all_cache(self, request: Request) -> Redirect:
        """Clear all application caches.

        Returns:
            Redirect back to cache management page
        """
        await enqueue_task("clear_cache", pattern="*")
        await enqueue_task("invalidate_page_response_cache", page_path=None)
        request.app.state.setdefault("flash_messages", []).append(
            {
                "type": "success",
                "message": "All cache clear tasks queued successfully.",
            }
        )
        return Redirect("/admin/settings/cache")

    @post("/cache/warm")
    async def warm_cache(self, request: Request) -> Redirect:
        """Warm all caches by pre-populating data.

        Returns:
            Redirect back to cache management page
        """
        await enqueue_task("warm_homepage_cache")
        await enqueue_task("warm_releases_cache")
        await enqueue_task("warm_events_cache")
        await enqueue_task("warm_blogs_cache")
        await enqueue_task("warm_pages_cache")
        request.app.state.setdefault("flash_messages", []).append(
            {
                "type": "success",
                "message": "Cache warming tasks queued successfully.",
            }
        )
        return Redirect("/admin/settings/cache")

    @get("/cache/keys/{category:str}")
    async def get_cache_keys(self, request: Request, category: str) -> Template:
        """Get list of cache keys for a specific category (HTMX partial).

        Args:
            request: The current request
            category: Category of keys to list (all, response, page, rate_limit)

        Returns:
            Template partial with key list
        """
        keys_data = await self._get_keys_by_category(request, category)
        return Template(
            template_name="admin/settings/partials/key_list.html.jinja2",
            context={
                "category": category,
                "keys": keys_data["keys"],
                "total": keys_data["total"],
                "truncated": keys_data["truncated"],
            },
        )

    @post("/cache/keys/{key:path}/delete")
    async def delete_cache_key(self, request: Request, key: str) -> Template:
        """Delete a specific cache key (HTMX action).

        Args:
            request: The current request
            key: The Redis key to delete

        Returns:
            Empty response or error message
        """
        try:
            store = request.app.stores.get("response_cache")
            if store and isinstance(store, RedisStore):
                redis = store._redis
                deleted = await redis.delete(key)
                if deleted:
                    return Template(
                        template_name="admin/settings/partials/key_deleted.html.jinja2",
                        context={"key": key, "success": True},
                    )
        except (ConnectionError, OSError, TimeoutError):
            pass

        return Template(
            template_name="admin/settings/partials/key_deleted.html.jinja2",
            context={"key": key, "success": False},
        )

    async def _get_keys_by_category(self, request: Request, category: str) -> dict:
        """Get keys filtered by category.

        Args:
            request: The current request
            category: Category filter (all, response, page, rate_limit)

        Returns:
            Dictionary with keys list and metadata
        """
        result = {"keys": [], "total": 0, "truncated": False}
        max_keys = 100

        try:
            store = request.app.stores.get("response_cache")
            if store and isinstance(store, RedisStore):
                redis = store._redis
                cursor = 0
                all_keys = []

                while True:
                    cursor, keys = await redis.scan(cursor, count=500)
                    for key in keys:
                        key_str = key.decode() if isinstance(key, bytes) else key
                        if category == "all":
                            all_keys.append(key_str)
                        elif category == "response":
                            if "page:" in key_str or "RESPONSE_CACHE" in key_str:
                                all_keys.append(key_str)
                        elif category == "page":
                            if key_str.startswith("pydotorg:cache:pages"):
                                all_keys.append(key_str)
                        elif category == "rate_limit" and "rate_limit" in key_str.lower():
                            all_keys.append(key_str)
                    if cursor == 0:
                        break

                result["total"] = len(all_keys)
                result["truncated"] = len(all_keys) > max_keys
                result["keys"] = sorted(all_keys[:max_keys])

        except (ConnectionError, OSError, TimeoutError):
            pass

        return result

    async def _get_cache_stats(self, request: Request) -> dict:
        """Get cache statistics from Redis.

        Args:
            request: The current request

        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "redis_connected": False,
            "total_keys": 0,
            "memory_used": "N/A",
            "memory_peak": "N/A",
            "hit_rate": "N/A",
            "page_cache_keys": 0,
            "response_cache_keys": 0,
            "rate_limit_keys": 0,
        }

        try:
            store = request.app.stores.get("response_cache")
            if store and isinstance(store, RedisStore):
                redis = store._redis
                info = await redis.info()

                stats["redis_connected"] = True
                stats["memory_used"] = info.get("used_memory_human", "N/A")
                stats["memory_peak"] = info.get("used_memory_peak_human", "N/A")

                hits = info.get("keyspace_hits", 0)
                misses = info.get("keyspace_misses", 0)
                total = hits + misses
                if total > 0:
                    stats["hit_rate"] = f"{(hits / total) * 100:.1f}%"

                cursor = 0
                page_keys = 0
                response_keys = 0
                rate_keys = 0
                total_keys = 0

                while True:
                    cursor, keys = await redis.scan(cursor, count=500)
                    total_keys += len(keys)
                    for key in keys:
                        key_str = key.decode() if isinstance(key, bytes) else key
                        if "page:" in key_str or "RESPONSE_CACHE" in key_str:
                            response_keys += 1
                        if key_str.startswith("pydotorg:cache:pages"):
                            page_keys += 1
                        if "rate_limit" in key_str.lower():
                            rate_keys += 1
                    if cursor == 0:
                        break

                stats["total_keys"] = total_keys
                stats["page_cache_keys"] = page_keys
                stats["response_cache_keys"] = response_keys
                stats["rate_limit_keys"] = rate_keys
        except (ConnectionError, OSError, TimeoutError):
            stats["redis_connected"] = False

        return stats

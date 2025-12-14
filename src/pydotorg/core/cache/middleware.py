"""Cache control middleware for HTTP headers.

Provides middleware for:
- Admin no-caching (private Cache-Control)
- Surrogate-Key headers for CDN purging (Fastly)
- Cache-Control headers for various content types
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.enums import ScopeType
from litestar.middleware import AbstractMiddleware

if TYPE_CHECKING:
    from litestar.types import ASGIApp, Message, Receive, Scope, Send

GLOBAL_SURROGATE_KEY = "pydotorg-app"


class AdminNoCacheMiddleware(AbstractMiddleware):
    """Middleware to prevent admin paths from being cached by CDN or browsers.

    Admin pages should never be cached to ensure users always see fresh content
    and prevent sensitive data from being stored in shared caches.
    """

    scopes = {ScopeType.HTTP}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process the request and add Cache-Control: private for admin paths."""
        path = scope.get("path", "")

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start" and path.startswith("/admin"):
                headers = list(message.get("headers", []))
                headers.append((b"cache-control", b"private, no-store"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


class SurrogateKeyMiddleware(AbstractMiddleware):
    """Middleware to add Surrogate-Key headers for CDN cache purging.

    Fastly and similar CDNs use Surrogate-Key headers to enable targeted
    cache invalidation. This middleware adds a global key to all responses
    and preserves any route-specific keys.

    Example:
        A response with Surrogate-Key: page-123 will be sent as:
        Surrogate-Key: pydotorg-app page-123

        This allows purging all cached content with the global key,
        or specific content with route-specific keys.
    """

    scopes = {ScopeType.HTTP}

    def __init__(self, app: ASGIApp, surrogate_key: str = GLOBAL_SURROGATE_KEY) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application.
            surrogate_key: Global surrogate key for all responses.
        """
        super().__init__(app)
        self.surrogate_key = surrogate_key

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process the request and add Surrogate-Key header."""

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                existing_key = headers.get(b"surrogate-key", b"").decode()

                keys = [self.surrogate_key]
                if existing_key:
                    keys.append(existing_key)

                new_headers = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"surrogate-key"]
                new_headers.append((b"surrogate-key", " ".join(keys).encode()))
                message["headers"] = new_headers

            await send(message)

        await self.app(scope, receive, send_wrapper)


class CacheControlMiddleware(AbstractMiddleware):
    """Middleware to add Cache-Control headers based on path patterns.

    Applies appropriate caching directives for different content types:
    - Static files: public, max-age=31536000 (1 year)
    - API responses: no-store (unless route specifies otherwise)
    - Pages: public, max-age=300 (5 minutes, overridable by route cache)
    """

    scopes = {ScopeType.HTTP}

    STATIC_PATHS = ("/static/", "/media/", "/assets/")
    API_PATHS = ("/api/",)
    NO_CACHE_PATHS = ("/admin/", "/auth/")

    STATIC_MAX_AGE = 31536000
    PAGE_MAX_AGE = 300

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process the request and add appropriate Cache-Control header."""
        path = scope.get("path", "")

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))

                if b"cache-control" not in headers:
                    cache_control = self._get_cache_control(path)
                    if cache_control:
                        new_headers = list(message.get("headers", []))
                        new_headers.append((b"cache-control", cache_control.encode()))
                        message["headers"] = new_headers

            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _get_cache_control(self, path: str) -> str | None:
        """Determine Cache-Control value based on path.

        Args:
            path: The request path.

        Returns:
            Cache-Control header value or None if not applicable.
        """
        if any(path.startswith(p) for p in self.NO_CACHE_PATHS):
            return "private, no-store"

        if any(path.startswith(p) for p in self.STATIC_PATHS):
            return f"public, max-age={self.STATIC_MAX_AGE}, immutable"

        if any(path.startswith(p) for p in self.API_PATHS):
            return "no-store"

        return f"public, max-age={self.PAGE_MAX_AGE}"


def create_cache_middleware_stack(
    *,
    enable_surrogate_keys: bool = True,
    surrogate_key: str = GLOBAL_SURROGATE_KEY,
) -> list[type[AbstractMiddleware]]:
    """Create the cache middleware stack for the application.

    Args:
        enable_surrogate_keys: Enable Surrogate-Key headers for CDN purging.
        surrogate_key: Global surrogate key value.

    Returns:
        List of middleware classes to add to the application.
    """
    middleware: list[type[AbstractMiddleware]] = [
        AdminNoCacheMiddleware,
        CacheControlMiddleware,
    ]

    if enable_surrogate_keys:
        middleware.append(SurrogateKeyMiddleware)

    return middleware

"""Middleware for injecting banners into request scope and API responses."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.middleware import MiddlewareProtocol
from sqlalchemy import or_, select

from pydotorg.domains.banners.models import Banner

if TYPE_CHECKING:
    from litestar import Litestar
    from litestar.types import ASGIApp, Message, Receive, Scope, Send
    from sqlalchemy.ext.asyncio import AsyncSession


def _matches_path(banner: Banner, request_path: str) -> bool:
    """Check if banner should show for the given path.

    If banner.paths is empty/None, banner shows on all routes.
    Otherwise, paths is a comma-separated list of path prefixes to match.
    """
    if not banner.paths:
        return True
    path_prefixes = [p.strip() for p in banner.paths.split(",") if p.strip()]
    if not path_prefixes:
        return True
    return any(request_path.startswith(prefix) or request_path == prefix.rstrip("/") for prefix in path_prefixes)


class SitewideBannerMiddleware(MiddlewareProtocol):
    """Middleware that populates banners in scope for template access.

    Frontend banners are available in templates via `request.scope['sitewide_banners']`.
    Shows banners that are sitewide OR target=frontend, filtered by paths if specified.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            accept = dict(scope.get("headers", [])).get(b"accept", b"").decode()
            if "text/html" in accept or not accept:
                path = scope.get("path", "/")
                banners = await self._get_frontend_banners(scope, path)
                scope["sitewide_banners"] = banners
            else:
                scope["sitewide_banners"] = []
        await self.app(scope, receive, send)

    @staticmethod
    async def _get_frontend_banners(scope: Scope, request_path: str) -> list[Banner]:
        """Fetch active banners for frontend pages (sitewide OR target=frontend)."""
        app: Litestar = scope["app"]
        plugin = app.plugins.get(SQLAlchemyPlugin)
        if plugin is None:
            return []
        config = plugin.config[0] if isinstance(plugin.config, list) else plugin.config
        async with config.get_session() as db_session:
            db_session: AsyncSession
            current_date = datetime.now(UTC).date()
            statement = select(Banner).where(
                Banner.is_active.is_(True),
                or_(Banner.is_sitewide.is_(True), Banner.target == "frontend"),
                (Banner.start_date.is_(None)) | (Banner.start_date <= current_date),
                (Banner.end_date.is_(None)) | (Banner.end_date >= current_date),
            )
            result = await db_session.execute(statement)
            all_banners = list(result.scalars().all())
            return [b for b in all_banners if _matches_path(b, request_path)]


class APIBannerMiddleware(MiddlewareProtocol):
    """Middleware that adds API banners as response headers.

    API banners (target=api or sitewide) are added as X-API-Notice headers.
    Useful for deprecation warnings, maintenance notices, etc.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        banners = await self._get_api_banners(scope, path)
        if not banners:
            await self.app(scope, receive, send)
            return

        notices = [{"type": b.banner_type, "title": b.title, "message": b.message, "link": b.link} for b in banners]

        async def send_with_banner(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"X-API-Notice", json.dumps(notices).encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_banner)

    @staticmethod
    async def _get_api_banners(scope: Scope, request_path: str) -> list[Banner]:
        """Fetch active banners for API routes (sitewide OR target=api)."""
        app: Litestar = scope["app"]
        plugin = app.plugins.get(SQLAlchemyPlugin)
        if plugin is None:
            return []
        config = plugin.config[0] if isinstance(plugin.config, list) else plugin.config
        async with config.get_session() as db_session:
            db_session: AsyncSession
            current_date = datetime.now(UTC).date()
            statement = select(Banner).where(
                Banner.is_active.is_(True),
                or_(Banner.is_sitewide.is_(True), Banner.target == "api"),
                (Banner.start_date.is_(None)) | (Banner.start_date <= current_date),
                (Banner.end_date.is_(None)) | (Banner.end_date >= current_date),
            )
            result = await db_session.execute(statement)
            all_banners = list(result.scalars().all())
            return [b for b in all_banners if _matches_path(b, request_path)]

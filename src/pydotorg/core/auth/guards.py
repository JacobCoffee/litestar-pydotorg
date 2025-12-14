"""Authentication and authorization guards."""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.exceptions import NotAuthorizedException, PermissionDeniedException

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler

    from pydotorg.domains.users.models import User

API_KEY_AUTH = "api_key"


def require_authenticated(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    if not connection.user:
        raise NotAuthorizedException("Authentication required")


def require_staff(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    require_authenticated(connection, _)
    user: User = connection.user

    if not user.is_staff:
        raise PermissionDeniedException("Staff privileges required")


def require_admin(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    require_authenticated(connection, _)
    user: User = connection.user

    if not user.is_superuser:
        raise PermissionDeniedException("Administrator privileges required")


def require_membership(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    require_authenticated(connection, _)
    user: User = connection.user

    if not user.has_membership:
        raise PermissionDeniedException("PSF membership required")


def require_higher_membership(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    require_membership(connection, _)
    user: User = connection.user

    if user.membership and user.membership.membership_type == "basic":
        raise PermissionDeniedException("Higher level PSF membership required")


def require_api_key(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Require API key authentication (not session/JWT)."""
    require_authenticated(connection, _)
    if connection.auth != API_KEY_AUTH:
        raise NotAuthorizedException("API key authentication required")


def require_api_key_or_staff(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Require API key authentication OR staff user with any auth method."""
    if not connection.user:
        raise NotAuthorizedException("Authentication required")

    user: User = connection.user
    if connection.auth == API_KEY_AUTH or user.is_staff:
        return

    raise PermissionDeniedException("API key or staff privileges required")

"""Authentication and authorization guards."""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.exceptions import NotAuthorizedException, PermissionDeniedException

from pydotorg.domains.users.models import MembershipType

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler

    from pydotorg.domains.users.models import User


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

    if user.membership and user.membership.membership_type == MembershipType.BASIC:
        raise PermissionDeniedException("Higher level PSF membership required")

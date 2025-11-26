"""Unit tests for admin guards."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException

from pydotorg.core.admin import require_admin_guard
from pydotorg.core.auth.guards import (
    require_admin,
    require_authenticated,
    require_higher_membership,
    require_membership,
    require_staff,
)
from pydotorg.domains.users.models import Membership, MembershipType, User


class TestRequireAuthenticated:
    """Tests for require_authenticated guard."""

    def test_authenticated_user_passes(self) -> None:
        """Authenticated user should pass the guard."""
        mock_user = Mock(spec=User)
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        require_authenticated(mock_connection, mock_handler)

    def test_unauthenticated_user_raises(self) -> None:
        """Unauthenticated user should raise NotAuthorizedException."""
        mock_connection = Mock()
        mock_connection.user = None
        mock_handler = Mock()

        with pytest.raises(NotAuthorizedException, match="Authentication required"):
            require_authenticated(mock_connection, mock_handler)


class TestRequireStaff:
    """Tests for require_staff guard."""

    def test_staff_user_passes(self) -> None:
        """Staff user should pass the guard."""
        mock_user = Mock(spec=User)
        mock_user.is_staff = True
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        require_staff(mock_connection, mock_handler)

    def test_non_staff_user_raises(self) -> None:
        """Non-staff user should raise PermissionDeniedException."""
        mock_user = Mock(spec=User)
        mock_user.is_staff = False
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        with pytest.raises(PermissionDeniedException, match="Staff privileges required"):
            require_staff(mock_connection, mock_handler)

    def test_unauthenticated_user_raises(self) -> None:
        """Unauthenticated user should raise NotAuthorizedException."""
        mock_connection = Mock()
        mock_connection.user = None
        mock_handler = Mock()

        with pytest.raises(NotAuthorizedException, match="Authentication required"):
            require_staff(mock_connection, mock_handler)


class TestRequireAdmin:
    """Tests for require_admin guard."""

    def test_admin_user_passes(self) -> None:
        """Admin (superuser) should pass the guard."""
        mock_user = Mock(spec=User)
        mock_user.is_superuser = True
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        require_admin(mock_connection, mock_handler)

    def test_non_admin_user_raises(self) -> None:
        """Non-admin user should raise PermissionDeniedException."""
        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        with pytest.raises(PermissionDeniedException, match="Administrator privileges required"):
            require_admin(mock_connection, mock_handler)

    def test_staff_but_not_admin_raises(self) -> None:
        """Staff user who is not admin should be denied."""
        mock_user = Mock(spec=User)
        mock_user.is_staff = True
        mock_user.is_superuser = False
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        with pytest.raises(PermissionDeniedException, match="Administrator privileges required"):
            require_admin(mock_connection, mock_handler)

    def test_unauthenticated_user_raises(self) -> None:
        """Unauthenticated user should raise NotAuthorizedException."""
        mock_connection = Mock()
        mock_connection.user = None
        mock_handler = Mock()

        with pytest.raises(NotAuthorizedException, match="Authentication required"):
            require_admin(mock_connection, mock_handler)


class TestRequireAdminGuard:
    """Tests for require_admin_guard (AdminController specific guard)."""

    def test_superuser_passes(self) -> None:
        """Superuser should pass the admin guard."""
        mock_user = Mock(spec=User)
        mock_user.is_superuser = True
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        require_admin_guard(mock_connection, mock_handler)

    def test_non_superuser_raises(self) -> None:
        """Non-superuser should raise PermissionDeniedException."""
        mock_user = Mock(spec=User)
        mock_user.is_superuser = False
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        with pytest.raises(PermissionDeniedException, match="Administrator privileges required"):
            require_admin_guard(mock_connection, mock_handler)

    def test_unauthenticated_raises(self) -> None:
        """Unauthenticated user should raise NotAuthorizedException."""
        mock_connection = Mock()
        mock_connection.user = None
        mock_handler = Mock()

        with pytest.raises(NotAuthorizedException, match="Authentication required"):
            require_admin_guard(mock_connection, mock_handler)


class TestRequireMembership:
    """Tests for require_membership guard."""

    def test_user_with_membership_passes(self) -> None:
        """User with membership should pass."""
        mock_membership = Mock(spec=Membership)
        mock_user = Mock(spec=User)
        mock_user.has_membership = True
        mock_user.membership = mock_membership
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        require_membership(mock_connection, mock_handler)

    def test_user_without_membership_raises(self) -> None:
        """User without membership should raise PermissionDeniedException."""
        mock_user = Mock(spec=User)
        mock_user.has_membership = False
        mock_user.membership = None
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        with pytest.raises(PermissionDeniedException, match="PSF membership required"):
            require_membership(mock_connection, mock_handler)

    def test_unauthenticated_user_raises(self) -> None:
        """Unauthenticated user should raise NotAuthorizedException."""
        mock_connection = Mock()
        mock_connection.user = None
        mock_handler = Mock()

        with pytest.raises(NotAuthorizedException, match="Authentication required"):
            require_membership(mock_connection, mock_handler)


class TestRequireHigherMembership:
    """Tests for require_higher_membership guard."""

    def test_supporting_membership_passes(self) -> None:
        """User with supporting membership should pass."""
        mock_membership = Mock(spec=Membership)
        mock_membership.membership_type = MembershipType.SUPPORTING
        mock_user = Mock(spec=User)
        mock_user.has_membership = True
        mock_user.membership = mock_membership
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        require_higher_membership(mock_connection, mock_handler)

    def test_fellow_membership_passes(self) -> None:
        """User with fellow membership should pass."""
        mock_membership = Mock(spec=Membership)
        mock_membership.membership_type = MembershipType.FELLOW
        mock_user = Mock(spec=User)
        mock_user.has_membership = True
        mock_user.membership = mock_membership
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        require_higher_membership(mock_connection, mock_handler)

    def test_basic_membership_raises(self) -> None:
        """User with basic membership should be denied."""
        mock_membership = Mock(spec=Membership)
        mock_membership.membership_type = MembershipType.BASIC
        mock_user = Mock(spec=User)
        mock_user.has_membership = True
        mock_user.membership = mock_membership
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        with pytest.raises(PermissionDeniedException, match="Higher level PSF membership required"):
            require_higher_membership(mock_connection, mock_handler)

    def test_no_membership_raises(self) -> None:
        """User without membership should raise PermissionDeniedException."""
        mock_user = Mock(spec=User)
        mock_user.has_membership = False
        mock_user.membership = None
        mock_connection = Mock()
        mock_connection.user = mock_user
        mock_handler = Mock()

        with pytest.raises(PermissionDeniedException, match="PSF membership required"):
            require_higher_membership(mock_connection, mock_handler)

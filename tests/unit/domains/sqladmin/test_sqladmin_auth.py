"""Unit tests for SQLAdmin authentication backend."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from pydotorg.domains.sqladmin.auth import AdminAuthBackend


class TestAdminAuthBackend:
    """Test cases for AdminAuthBackend."""

    @pytest.fixture
    def auth_backend(self) -> AdminAuthBackend:
        """Create an AdminAuthBackend instance for testing."""
        with patch("pydotorg.domains.sqladmin.auth.SessionService"):
            backend = AdminAuthBackend(secret_key="test-secret-key-12345")
            backend._litestar_session_service = MagicMock()
            backend._litestar_session_service.get_user_id_from_session.return_value = None
            return backend

    @pytest.fixture
    def mock_request(self) -> MagicMock:
        """Create a mock Starlette request."""
        request = MagicMock()
        request.session = {}
        request.cookies = {}
        return request

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        """Create a mock User object."""
        user = MagicMock()
        user.id = uuid4()
        user.username = "admin"
        user.is_superuser = True
        user.is_active = True
        user.password_hash = "$2b$12$test_hash_that_looks_valid"
        return user

    async def test_login_missing_username(
        self, auth_backend: AdminAuthBackend, mock_request: MagicMock
    ) -> None:
        """Test that login fails when username is missing."""
        mock_request.form = AsyncMock(return_value={"password": "test"})
        result = await auth_backend.login(mock_request)
        assert result is False

    async def test_login_missing_password(
        self, auth_backend: AdminAuthBackend, mock_request: MagicMock
    ) -> None:
        """Test that login fails when password is missing."""
        mock_request.form = AsyncMock(return_value={"username": "admin"})
        result = await auth_backend.login(mock_request)
        assert result is False

    async def test_login_user_not_found(
        self, auth_backend: AdminAuthBackend, mock_request: MagicMock
    ) -> None:
        """Test that login fails when user is not found."""
        mock_request.form = AsyncMock(
            return_value={"username": "nonexistent", "password": "test"}
        )

        with patch.object(auth_backend, "_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await auth_backend.login(mock_request)
            assert result is False

    async def test_login_user_not_superuser(
        self,
        auth_backend: AdminAuthBackend,
        mock_request: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test that login fails when user is not a superuser."""
        mock_user.is_superuser = False
        mock_request.form = AsyncMock(
            return_value={"username": "admin", "password": "test"}
        )

        with patch.object(auth_backend, "_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await auth_backend.login(mock_request)
            assert result is False

    async def test_login_no_password_hash(
        self,
        auth_backend: AdminAuthBackend,
        mock_request: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test that login fails when user has no password hash."""
        mock_user.password_hash = None
        mock_request.form = AsyncMock(
            return_value={"username": "admin", "password": "test"}
        )

        with patch.object(auth_backend, "_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await auth_backend.login(mock_request)
            assert result is False

    async def test_login_wrong_password(
        self,
        auth_backend: AdminAuthBackend,
        mock_request: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test that login fails with wrong password."""
        mock_request.form = AsyncMock(
            return_value={"username": "admin", "password": "wrong_password"}
        )

        with (
            patch.object(auth_backend, "_session_maker") as mock_session_maker,
            patch(
                "pydotorg.domains.sqladmin.auth.verify_password", return_value=False
            ),
        ):
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await auth_backend.login(mock_request)
            assert result is False

    async def test_login_success(
        self,
        auth_backend: AdminAuthBackend,
        mock_request: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test that login succeeds with correct credentials."""
        mock_request.form = AsyncMock(
            return_value={"username": "admin", "password": "correct_password"}
        )

        with (
            patch.object(auth_backend, "_session_maker") as mock_session_maker,
            patch("pydotorg.domains.sqladmin.auth.verify_password", return_value=True),
        ):
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await auth_backend.login(mock_request)
            assert result is True
            assert mock_request.session["user_id"] == str(mock_user.id)
            assert mock_request.session["is_admin"] is True

    async def test_logout_clears_session(
        self, auth_backend: AdminAuthBackend, mock_request: MagicMock
    ) -> None:
        """Test that logout clears the session."""
        mock_request.session = {"user_id": "123", "is_admin": True}
        result = await auth_backend.logout(mock_request)
        assert result is True
        assert mock_request.session == {}

    async def test_authenticate_missing_user_id(
        self, auth_backend: AdminAuthBackend, mock_request: MagicMock
    ) -> None:
        """Test that authenticate fails when user_id is missing."""
        mock_request.session = {"is_admin": True}
        result = await auth_backend.authenticate(mock_request)
        assert result is False

    async def test_authenticate_missing_is_admin(
        self, auth_backend: AdminAuthBackend, mock_request: MagicMock
    ) -> None:
        """Test that authenticate fails when is_admin is missing."""
        test_uuid = uuid4()
        mock_request.session = {"user_id": str(test_uuid)}
        result = await auth_backend.authenticate(mock_request)
        assert result is False

    async def test_authenticate_user_not_found(
        self, auth_backend: AdminAuthBackend, mock_request: MagicMock
    ) -> None:
        """Test that authenticate fails when user is not found."""
        test_uuid = uuid4()
        mock_request.session = {"user_id": str(test_uuid), "is_admin": True}

        with patch.object(auth_backend, "_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await auth_backend.authenticate(mock_request)
            assert result is False

    async def test_authenticate_user_not_superuser(
        self,
        auth_backend: AdminAuthBackend,
        mock_request: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test that authenticate fails when user is not a superuser."""
        mock_user.is_superuser = False
        mock_request.session = {"user_id": str(mock_user.id), "is_admin": True}

        with patch.object(auth_backend, "_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await auth_backend.authenticate(mock_request)
            assert result is False

    async def test_authenticate_user_not_active(
        self,
        auth_backend: AdminAuthBackend,
        mock_request: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test that authenticate fails when user is not active."""
        mock_user.is_active = False
        mock_request.session = {"user_id": str(mock_user.id), "is_admin": True}

        with patch.object(auth_backend, "_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await auth_backend.authenticate(mock_request)
            assert result is False

    async def test_authenticate_success(
        self,
        auth_backend: AdminAuthBackend,
        mock_request: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test that authenticate succeeds with valid session and user."""
        mock_request.session = {"user_id": str(mock_user.id), "is_admin": True}

        with patch.object(auth_backend, "_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await auth_backend.authenticate(mock_request)
            assert result is True

    async def test_authenticate_via_litestar_session(
        self,
        auth_backend: AdminAuthBackend,
        mock_request: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test that authenticate succeeds via Litestar session (SSO)."""
        mock_request.session = {}
        mock_request.cookies = {"session_id": "valid-session-token"}

        auth_backend._litestar_session_service.get_user_id_from_session.return_value = (
            mock_user.id
        )

        with patch.object(auth_backend, "_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await auth_backend.authenticate(mock_request)
            assert result is True
            assert mock_request.session["user_id"] == str(mock_user.id)
            assert mock_request.session["is_admin"] is True

    async def test_authenticate_litestar_session_not_superuser(
        self,
        auth_backend: AdminAuthBackend,
        mock_request: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test that Litestar session auth fails for non-superusers."""
        mock_user.is_superuser = False
        mock_request.session = {}
        mock_request.cookies = {"session_id": "valid-session-token"}

        auth_backend._litestar_session_service.get_user_id_from_session.return_value = (
            mock_user.id
        )

        with patch.object(auth_backend, "_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_session_maker.return_value.__aexit__.return_value = None

            result = await auth_backend.authenticate(mock_request)
            assert result is False

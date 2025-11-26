"""Unit tests for UserAdminService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest

from pydotorg.domains.admin.schemas import UserStaffUpdate
from pydotorg.domains.admin.services.users import UserAdminService
from pydotorg.domains.users.models import User


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock async session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_user() -> Mock:
    """Create a mock user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.is_active = True
    user.is_staff = False
    user.is_superuser = False
    user.email_verified = True
    user.oauth_provider = None
    user.oauth_id = None
    user.date_joined = None
    user.last_login = None
    user.bio = ""
    user.search_visibility = "public"
    user.email_privacy = "private"
    user.public_profile = True
    user.created_at = None
    user.updated_at = None
    return user


@pytest.fixture
def service(mock_session: AsyncMock) -> UserAdminService:
    """Create a UserAdminService instance with mock session."""
    return UserAdminService(session=mock_session)


class TestListUsers:
    """Tests for UserAdminService.list_users."""

    async def test_list_users_returns_users_and_count(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test that list_users returns users and total count."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_users_result = MagicMock()
        mock_users_result.scalars.return_value.all.return_value = [mock_user]

        mock_session.execute.side_effect = [mock_count_result, mock_users_result]

        users, total = await service.list_users()

        assert total == 1
        assert len(users) == 1
        assert users[0] == mock_user

    async def test_list_users_with_search(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test list_users with search filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_users_result = MagicMock()
        mock_users_result.scalars.return_value.all.return_value = [mock_user]

        mock_session.execute.side_effect = [mock_count_result, mock_users_result]

        _users, total = await service.list_users(search="test")

        assert total == 1
        assert mock_session.execute.call_count == 2

    async def test_list_users_with_staff_filter(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test list_users with staff filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_users_result = MagicMock()
        mock_users_result.scalars.return_value.all.return_value = [mock_user]

        mock_session.execute.side_effect = [mock_count_result, mock_users_result]

        _users, total = await service.list_users(filter_by="staff")

        assert total == 1

    async def test_list_users_with_pagination(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test list_users with pagination."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100

        mock_users_result = MagicMock()
        mock_users_result.scalars.return_value.all.return_value = [mock_user]

        mock_session.execute.side_effect = [mock_count_result, mock_users_result]

        users, total = await service.list_users(limit=10, offset=20)

        assert total == 100
        assert len(users) == 1

    async def test_list_users_empty_result(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test list_users with no results."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_users_result = MagicMock()
        mock_users_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_users_result]

        users, total = await service.list_users()

        assert total == 0
        assert len(users) == 0


class TestGetUser:
    """Tests for UserAdminService.get_user."""

    async def test_get_user_found(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test get_user returns user when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        user = await service.get_user(mock_user.id)

        assert user == mock_user

    async def test_get_user_not_found(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test get_user returns None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        user = await service.get_user(uuid4())

        assert user is None


class TestUpdateUserStatus:
    """Tests for UserAdminService.update_user_status."""

    async def test_update_user_status_success(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test updating user status."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        update_data = UserStaffUpdate(is_staff=True)
        user = await service.update_user_status(mock_user.id, update_data)

        assert user.is_staff is True
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_user)

    async def test_update_user_status_not_found(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test updating status for non-existent user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        update_data = UserStaffUpdate(is_staff=True)
        user = await service.update_user_status(uuid4(), update_data)

        assert user is None
        mock_session.commit.assert_not_called()


class TestToggleMethods:
    """Tests for toggle methods."""

    async def test_toggle_staff(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test toggle_staff flips the is_staff flag."""
        mock_user.is_staff = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        user = await service.toggle_staff(mock_user.id)

        assert user.is_staff is True
        mock_session.commit.assert_called_once()

    async def test_toggle_superuser(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test toggle_superuser flips the is_superuser flag."""
        mock_user.is_superuser = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        user = await service.toggle_superuser(mock_user.id)

        assert user.is_superuser is True
        mock_session.commit.assert_called_once()

    async def test_toggle_active(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test toggle_active flips the is_active flag."""
        mock_user.is_active = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        user = await service.toggle_active(mock_user.id)

        assert user.is_active is False
        mock_session.commit.assert_called_once()


class TestActivateDeactivate:
    """Tests for activate/deactivate methods."""

    async def test_activate_user(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test activate_user sets is_active to True."""
        mock_user.is_active = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        user = await service.activate_user(mock_user.id)

        assert user.is_active is True

    async def test_deactivate_user(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test deactivate_user sets is_active to False."""
        mock_user.is_active = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        user = await service.deactivate_user(mock_user.id)

        assert user.is_active is False


class TestDeleteUser:
    """Tests for UserAdminService.delete_user."""

    async def test_delete_user_success(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test deleting existing user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        result = await service.delete_user(mock_user.id)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_user)
        mock_session.commit.assert_called_once()

    async def test_delete_user_not_found(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test deleting non-existent user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.delete_user(uuid4())

        assert result is False
        mock_session.delete.assert_not_called()


class TestUpdateUser:
    """Tests for UserAdminService.update_user."""

    async def test_update_user_all_fields(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test updating all user fields."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        user = await service.update_user(
            mock_user.id,
            first_name="New",
            last_name="Name",
            email="new@example.com",
            is_active=False,
            is_staff=True,
            is_superuser=True,
        )

        assert user.first_name == "New"
        assert user.last_name == "Name"
        assert user.email == "new@example.com"
        assert user.is_active is False
        assert user.is_staff is True
        assert user.is_superuser is True
        mock_session.commit.assert_called_once()

    async def test_update_user_partial(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """Test partial user update."""
        original_email = mock_user.email
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        user = await service.update_user(
            mock_user.id,
            first_name="Updated",
        )

        assert user.first_name == "Updated"
        assert user.email == original_email
        mock_session.commit.assert_called_once()

    async def test_update_user_not_found(
        self,
        service: UserAdminService,
        mock_session: AsyncMock,
    ) -> None:
        """Test updating non-existent user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        user = await service.update_user(
            uuid4(),
            first_name="Test",
        )

        assert user is None
        mock_session.commit.assert_not_called()

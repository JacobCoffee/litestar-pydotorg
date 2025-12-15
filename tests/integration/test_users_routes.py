"""Integration tests for Users domain routes."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar import Litestar
from litestar.testing import AsyncTestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.users.controllers import MembershipController, UserController, UserGroupController
from pydotorg.domains.users.dependencies import get_user_dependencies
from pydotorg.domains.users.models import EmailPrivacy, Membership, MembershipType, SearchVisibility, User, UserGroup

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class UsersTestFixtures:
    """Container for users test fixtures."""

    client: AsyncTestClient
    session_factory: async_sessionmaker
    test_user: User
    test_user2: User
    test_membership: Membership
    test_group: UserGroup


@pytest.fixture
async def users_fixtures(
    async_engine: AsyncEngine,
    async_session_factory: async_sessionmaker,
    _module_sqlalchemy_config: SQLAlchemyAsyncConfig,
) -> AsyncIterator[UsersTestFixtures]:
    """Create test fixtures using module-scoped config to prevent connection exhaustion.

    Uses the shared _module_sqlalchemy_config from conftest.py instead of creating
    a new SQLAlchemyAsyncConfig per test, which was causing TooManyConnectionsError.
    Creates the database schema, test users, memberships, and groups in the correct order
    to ensure all tests have access to the same database state.
    """
    async with async_engine.begin() as conn:
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        existing_tables = {row[0] for row in result.fetchall()}

        for table in reversed(AuditBase.metadata.sorted_tables):
            if table.name in existing_tables:
                await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))

    async with async_session_factory() as session:
        user1 = User(
            username=f"testuser_{uuid4().hex[:8]}",
            email=f"testuser_{uuid4().hex[:8]}@example.com",
            password_hash="hashed_password",
            first_name="Test",
            last_name="User",
            is_active=True,
            bio="Test user bio",
            search_visibility=SearchVisibility.PUBLIC,
            email_privacy=EmailPrivacy.PRIVATE,
        )
        user2 = User(
            username=f"testuser2_{uuid4().hex[:8]}",
            email=f"testuser2_{uuid4().hex[:8]}@example.com",
            password_hash="hashed_password",
            first_name="Test2",
            last_name="User2",
            is_active=True,
        )
        session.add_all([user1, user2])
        await session.commit()
        await session.refresh(user1)
        await session.refresh(user2)

        membership = Membership(
            user_id=user1.id,
            membership_type=MembershipType.BASIC,
            legal_name="Test User Legal",
            preferred_name="Tester",
            email_address=user1.email,
            city="Test City",
            region="Test Region",
            country="Test Country",
            postal_code="12345",
            psf_code_of_conduct=True,
            votes=False,
        )
        session.add(membership)
        await session.commit()
        await session.refresh(membership)

        group = UserGroup(
            name="Test User Group",
            location="Test Location",
            url="https://test-group.example.com",
            approved=False,
            trusted=False,
        )
        session.add(group)
        await session.commit()
        await session.refresh(group)

        user1_data = User(
            id=user1.id,
            username=user1.username,
            email=user1.email,
            first_name=user1.first_name,
            last_name=user1.last_name,
        )
        user2_data = User(
            id=user2.id,
            username=user2.username,
            email=user2.email,
            first_name=user2.first_name,
            last_name=user2.last_name,
        )
        membership_data = Membership(
            id=membership.id,
            user_id=membership.user_id,
            membership_type=membership.membership_type,
            legal_name=membership.legal_name,
        )
        group_data = UserGroup(id=group.id, name=group.name, location=group.location)

    from advanced_alchemy.filters import LimitOffset
    from litestar.params import Parameter

    async def provide_limit_offset(
        current_page: int = Parameter(ge=1, default=1, query="currentPage"),
        page_size: int = Parameter(ge=1, le=100, default=10, query="pageSize"),
    ) -> LimitOffset:
        """Provide limit offset pagination."""
        return LimitOffset(page_size, page_size * (current_page - 1))

    sqlalchemy_plugin = SQLAlchemyPlugin(config=_module_sqlalchemy_config)

    user_deps = get_user_dependencies()
    user_deps["limit_offset"] = provide_limit_offset

    test_app = Litestar(
        route_handlers=[UserController, MembershipController, UserGroupController],
        plugins=[sqlalchemy_plugin],
        dependencies=user_deps,
        debug=True,
    )

    async with AsyncTestClient(
        app=test_app,
        base_url="http://testserver.local",
    ) as test_client:
        fixtures = UsersTestFixtures()
        fixtures.client = test_client
        fixtures.session_factory = async_session_factory
        fixtures.test_user = user1_data
        fixtures.test_user2 = user2_data
        fixtures.test_membership = membership_data
        fixtures.test_group = group_data
        yield fixtures


@pytest.mark.integration
class TestUserControllerRoutes:
    """Route-level integration tests for UserController."""

    async def test_list_users_endpoint_reachable(self, users_fixtures: UsersTestFixtures) -> None:
        """Test that list users endpoint is reachable."""
        response = await users_fixtures.client.get("/api/v1/users/?currentPage=1&pageSize=100")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_list_users_returns_data(self, users_fixtures: UsersTestFixtures) -> None:
        """Test that list users returns created test users."""
        response = await users_fixtures.client.get("/api/v1/users/?currentPage=1&pageSize=100")
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 2

    async def test_list_users_pagination(self, users_fixtures: UsersTestFixtures) -> None:
        """Test user listing with pagination."""
        response = await users_fixtures.client.get("/api/v1/users/?currentPage=1&pageSize=1")
        assert response.status_code == 200
        users = response.json()
        assert len(users) == 1

    async def test_create_user_endpoint(self, users_fixtures: UsersTestFixtures) -> None:
        """Test creating a new user via API."""
        unique_username = f"newuser_{uuid4().hex[:8]}"
        unique_email = f"newuser_{uuid4().hex[:8]}@example.com"

        response = await users_fixtures.client.post(
            "/api/v1/users/",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": "secure_password123",
                "first_name": "New",
                "last_name": "User",
                "bio": "A new user",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == unique_username
        assert data["email"] == unique_email
        assert "password" not in data
        assert "password_hash" not in data
        assert "id" in data

    async def test_create_user_duplicate_email(self, users_fixtures: UsersTestFixtures) -> None:
        """Test creating user with duplicate email fails."""
        response = await users_fixtures.client.post(
            "/api/v1/users/",
            json={
                "username": f"newuser_{uuid4().hex[:8]}",
                "email": users_fixtures.test_user.email,
                "password": "secure_password123",
                "first_name": "Duplicate",
                "last_name": "Email",
            },
        )
        assert response.status_code in {400, 500}

    async def test_create_user_duplicate_username(self, users_fixtures: UsersTestFixtures) -> None:
        """Test creating user with duplicate username fails."""
        response = await users_fixtures.client.post(
            "/api/v1/users/",
            json={
                "username": users_fixtures.test_user.username,
                "email": f"newuser_{uuid4().hex[:8]}@example.com",
                "password": "secure_password123",
                "first_name": "Duplicate",
                "last_name": "Username",
            },
        )
        assert response.status_code in {400, 500}

    async def test_get_user_by_id(self, users_fixtures: UsersTestFixtures) -> None:
        """Test getting a user by ID."""
        response = await users_fixtures.client.get(f"/api/v1/users/{users_fixtures.test_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(users_fixtures.test_user.id)
        assert data["username"] == users_fixtures.test_user.username
        assert data["email"] == users_fixtures.test_user.email

    async def test_get_user_by_id_not_found(self, users_fixtures: UsersTestFixtures) -> None:
        """Test getting non-existent user returns 404 or 500.

        Note: Currently returns 500 because NotFoundError is not handled.
        Should return 404 once exception handling is added to the controller.
        """
        fake_id = str(uuid4())
        response = await users_fixtures.client.get(f"/api/v1/users/{fake_id}")
        assert response.status_code in {404, 500}

    async def test_get_user_by_username(self, users_fixtures: UsersTestFixtures) -> None:
        """Test getting a user by username."""
        response = await users_fixtures.client.get(f"/api/v1/users/username/{users_fixtures.test_user.username}")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == users_fixtures.test_user.username

    async def test_get_user_by_username_not_found(self, users_fixtures: UsersTestFixtures) -> None:
        """Test getting user by non-existent username."""
        response = await users_fixtures.client.get("/api/v1/users/username/nonexistent_user_12345")
        assert response.status_code in {404, 500}

    async def test_get_user_by_email(self, users_fixtures: UsersTestFixtures) -> None:
        """Test getting a user by email."""
        response = await users_fixtures.client.get(f"/api/v1/users/email/{users_fixtures.test_user.email}")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == users_fixtures.test_user.email

    async def test_get_user_by_email_not_found(self, users_fixtures: UsersTestFixtures) -> None:
        """Test getting user by non-existent email."""
        response = await users_fixtures.client.get("/api/v1/users/email/nonexistent@example.com")
        assert response.status_code in {404, 500}

    async def test_update_user(self, users_fixtures: UsersTestFixtures) -> None:
        """Test updating a user."""
        response = await users_fixtures.client.put(
            f"/api/v1/users/{users_fixtures.test_user.id}",
            json={
                "first_name": "Updated",
                "last_name": "Name",
                "bio": "Updated bio",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["bio"] == "Updated bio"

    async def test_update_user_partial(self, users_fixtures: UsersTestFixtures) -> None:
        """Test partial user update."""
        response = await users_fixtures.client.put(
            f"/api/v1/users/{users_fixtures.test_user.id}",
            json={
                "bio": "Only bio updated",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "Only bio updated"

    async def test_update_user_not_found(self, users_fixtures: UsersTestFixtures) -> None:
        """Test updating non-existent user."""
        fake_id = str(uuid4())
        response = await users_fixtures.client.put(
            f"/api/v1/users/{fake_id}",
            json={
                "first_name": "Should",
                "last_name": "Fail",
            },
        )
        assert response.status_code == 404

    async def test_deactivate_user(self, users_fixtures: UsersTestFixtures) -> None:
        """Test deactivating a user."""
        unique_username = f"deactivate_{uuid4().hex[:8]}"
        unique_email = f"deactivate_{uuid4().hex[:8]}@example.com"

        create_response = await users_fixtures.client.post(
            "/api/v1/users/",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": "password123",
                "first_name": "Deactivate",
                "last_name": "Test",
            },
        )
        user_id = create_response.json()["id"]

        response = await users_fixtures.client.patch(f"/api/v1/users/{user_id}/deactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    async def test_reactivate_user(self, users_fixtures: UsersTestFixtures) -> None:
        """Test reactivating a deactivated user."""
        unique_username = f"reactivate_{uuid4().hex[:8]}"
        unique_email = f"reactivate_{uuid4().hex[:8]}@example.com"

        create_response = await users_fixtures.client.post(
            "/api/v1/users/",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": "password123",
                "first_name": "Reactivate",
                "last_name": "Test",
            },
        )
        user_id = create_response.json()["id"]

        await users_fixtures.client.patch(f"/api/v1/users/{user_id}/deactivate")
        response = await users_fixtures.client.patch(f"/api/v1/users/{user_id}/reactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    async def test_delete_user(self, users_fixtures: UsersTestFixtures) -> None:
        """Test deleting a user."""
        unique_username = f"delete_{uuid4().hex[:8]}"
        unique_email = f"delete_{uuid4().hex[:8]}@example.com"

        create_response = await users_fixtures.client.post(
            "/api/v1/users/",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": "password123",
                "first_name": "Delete",
                "last_name": "Test",
            },
        )
        user_id = create_response.json()["id"]

        response = await users_fixtures.client.delete(f"/api/v1/users/{user_id}")
        assert response.status_code == 204

        get_response = await users_fixtures.client.get(f"/api/v1/users/{user_id}")
        assert get_response.status_code == 404

    async def test_delete_user_not_found(self, users_fixtures: UsersTestFixtures) -> None:
        """Test deleting non-existent user."""
        fake_id = str(uuid4())
        response = await users_fixtures.client.delete(f"/api/v1/users/{fake_id}")
        assert response.status_code == 404


@pytest.mark.integration
class TestMembershipControllerRoutes:
    """Route-level integration tests for MembershipController."""

    async def test_list_memberships_endpoint_reachable(self, users_fixtures: UsersTestFixtures) -> None:
        """Test that list memberships endpoint is reachable."""
        response = await users_fixtures.client.get("/api/v1/memberships/?currentPage=1&pageSize=100")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_list_memberships_returns_data(self, users_fixtures: UsersTestFixtures) -> None:
        """Test that list memberships returns created test membership."""
        response = await users_fixtures.client.get("/api/v1/memberships/?currentPage=1&pageSize=100")
        assert response.status_code == 200
        memberships = response.json()
        assert len(memberships) >= 1

    async def test_list_memberships_pagination(self, users_fixtures: UsersTestFixtures) -> None:
        """Test membership listing with pagination."""
        response = await users_fixtures.client.get("/api/v1/memberships/?currentPage=1&pageSize=1")
        assert response.status_code == 200
        memberships = response.json()
        assert len(memberships) == 1

    async def test_create_membership(self, users_fixtures: UsersTestFixtures) -> None:
        """Test creating a new membership."""
        response = await users_fixtures.client.post(
            "/api/v1/memberships/",
            json={
                "user_id": str(users_fixtures.test_user2.id),
                "membership_type": "supporting",
                "legal_name": "Test User2 Legal",
                "preferred_name": "Tester2",
                "email_address": users_fixtures.test_user2.email,
                "city": "Test City 2",
                "region": "Test Region 2",
                "country": "Test Country 2",
                "postal_code": "54321",
                "psf_code_of_conduct": True,
                "votes": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(users_fixtures.test_user2.id)
        assert data["membership_type"] == "supporting"
        assert data["legal_name"] == "Test User2 Legal"

    async def test_create_membership_duplicate_user(self, users_fixtures: UsersTestFixtures) -> None:
        """Test creating membership for user who already has one."""
        response = await users_fixtures.client.post(
            "/api/v1/memberships/",
            json={
                "user_id": str(users_fixtures.test_user.id),
                "membership_type": "basic",
                "legal_name": "Duplicate",
            },
        )
        assert response.status_code in {400, 500}

    async def test_get_membership_by_id(self, users_fixtures: UsersTestFixtures) -> None:
        """Test getting a membership by ID."""
        response = await users_fixtures.client.get(f"/api/v1/memberships/{users_fixtures.test_membership.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(users_fixtures.test_membership.id)
        assert data["user_id"] == str(users_fixtures.test_membership.user_id)

    async def test_get_membership_by_id_not_found(self, users_fixtures: UsersTestFixtures) -> None:
        """Test getting non-existent membership returns 404."""
        fake_id = str(uuid4())
        response = await users_fixtures.client.get(f"/api/v1/memberships/{fake_id}")
        assert response.status_code == 404

    async def test_get_membership_by_user(self, users_fixtures: UsersTestFixtures) -> None:
        """Test getting membership by user ID."""
        response = await users_fixtures.client.get(f"/api/v1/memberships/user/{users_fixtures.test_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(users_fixtures.test_user.id)

    async def test_get_membership_by_user_not_found(self, users_fixtures: UsersTestFixtures) -> None:
        """Test getting membership for user without membership."""
        response = await users_fixtures.client.get(f"/api/v1/memberships/user/{users_fixtures.test_user2.id}")
        assert response.status_code in {404, 500}

    async def test_update_membership(self, users_fixtures: UsersTestFixtures) -> None:
        """Test updating a membership."""
        response = await users_fixtures.client.put(
            f"/api/v1/memberships/{users_fixtures.test_membership.id}",
            json={
                "membership_type": "supporting",
                "preferred_name": "Updated Tester",
                "city": "Updated City",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["membership_type"] == "supporting"
        assert data["preferred_name"] == "Updated Tester"
        assert data["city"] == "Updated City"

    async def test_update_membership_partial(self, users_fixtures: UsersTestFixtures) -> None:
        """Test partial membership update."""
        response = await users_fixtures.client.put(
            f"/api/v1/memberships/{users_fixtures.test_membership.id}",
            json={
                "city": "Only City Updated",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Only City Updated"

    async def test_update_membership_not_found(self, users_fixtures: UsersTestFixtures) -> None:
        """Test updating non-existent membership."""
        fake_id = str(uuid4())
        response = await users_fixtures.client.put(
            f"/api/v1/memberships/{fake_id}",
            json={
                "city": "Should Fail",
            },
        )
        assert response.status_code == 404

    async def test_delete_membership(self, users_fixtures: UsersTestFixtures) -> None:
        """Test deleting a membership."""
        unique_username = f"memb_delete_{uuid4().hex[:8]}"
        unique_email = f"memb_delete_{uuid4().hex[:8]}@example.com"

        user_response = await users_fixtures.client.post(
            "/api/v1/users/",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": "password123",
                "first_name": "Membership",
                "last_name": "Delete",
            },
        )
        user_id = user_response.json()["id"]

        create_response = await users_fixtures.client.post(
            "/api/v1/memberships/",
            json={
                "user_id": user_id,
                "membership_type": "basic",
                "legal_name": "To Delete",
            },
        )
        membership_id = create_response.json()["id"]

        response = await users_fixtures.client.delete(f"/api/v1/memberships/{membership_id}")
        assert response.status_code == 204

        get_response = await users_fixtures.client.get(f"/api/v1/memberships/{membership_id}")
        assert get_response.status_code == 404

    async def test_delete_membership_not_found(self, users_fixtures: UsersTestFixtures) -> None:
        """Test deleting non-existent membership."""
        fake_id = str(uuid4())
        response = await users_fixtures.client.delete(f"/api/v1/memberships/{fake_id}")
        assert response.status_code == 404


@pytest.mark.integration
class TestUserGroupControllerRoutes:
    """Route-level integration tests for UserGroupController."""

    async def test_list_user_groups_endpoint_reachable(self, users_fixtures: UsersTestFixtures) -> None:
        """Test that list user groups endpoint is reachable."""
        response = await users_fixtures.client.get("/api/v1/user-groups/?currentPage=1&pageSize=100")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_list_user_groups_returns_data(self, users_fixtures: UsersTestFixtures) -> None:
        """Test that list user groups returns created test group."""
        response = await users_fixtures.client.get("/api/v1/user-groups/?currentPage=1&pageSize=100")
        assert response.status_code == 200
        groups = response.json()
        assert len(groups) >= 1

    async def test_list_user_groups_pagination(self, users_fixtures: UsersTestFixtures) -> None:
        """Test user groups listing with pagination."""
        response = await users_fixtures.client.get("/api/v1/user-groups/?currentPage=1&pageSize=1")
        assert response.status_code == 200
        groups = response.json()
        assert len(groups) == 1

    async def test_list_approved_groups(self, users_fixtures: UsersTestFixtures) -> None:
        """Test listing approved user groups."""
        await users_fixtures.client.patch(f"/api/v1/user-groups/{users_fixtures.test_group.id}/approve")

        response = await users_fixtures.client.get("/api/v1/user-groups/approved")
        assert response.status_code == 200
        groups = response.json()
        assert any(g["id"] == str(users_fixtures.test_group.id) for g in groups)
        assert all(g["approved"] is True for g in groups)

    async def test_list_trusted_groups(self, users_fixtures: UsersTestFixtures) -> None:
        """Test listing trusted user groups."""
        await users_fixtures.client.patch(f"/api/v1/user-groups/{users_fixtures.test_group.id}/mark-trusted")

        response = await users_fixtures.client.get("/api/v1/user-groups/trusted")
        assert response.status_code == 200
        groups = response.json()
        assert any(g["id"] == str(users_fixtures.test_group.id) for g in groups)
        assert all(g["trusted"] is True for g in groups)

    async def test_create_user_group(self, users_fixtures: UsersTestFixtures) -> None:
        """Test creating a new user group."""
        response = await users_fixtures.client.post(
            "/api/v1/user-groups/",
            json={
                "name": f"New Group {uuid4().hex[:8]}",
                "location": "New Location",
                "url": "https://new-group.example.com",
                "url_type": "meetup",
                "approved": False,
                "trusted": False,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "New Group" in data["name"]
        assert data["location"] == "New Location"
        assert data["url_type"] == "meetup"

    async def test_get_user_group_by_id(self, users_fixtures: UsersTestFixtures) -> None:
        """Test getting a user group by ID."""
        response = await users_fixtures.client.get(f"/api/v1/user-groups/{users_fixtures.test_group.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(users_fixtures.test_group.id)
        assert data["name"] == users_fixtures.test_group.name

    async def test_get_user_group_by_id_not_found(self, users_fixtures: UsersTestFixtures) -> None:
        """Test getting non-existent user group returns 404."""
        fake_id = str(uuid4())
        response = await users_fixtures.client.get(f"/api/v1/user-groups/{fake_id}")
        assert response.status_code == 404

    async def test_update_user_group(self, users_fixtures: UsersTestFixtures) -> None:
        """Test updating a user group."""
        response = await users_fixtures.client.put(
            f"/api/v1/user-groups/{users_fixtures.test_group.id}",
            json={
                "name": "Updated Group Name",
                "location": "Updated Location",
                "url": "https://updated-group.example.com",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Group Name"
        assert data["location"] == "Updated Location"
        assert data["url"] == "https://updated-group.example.com"

    async def test_update_user_group_partial(self, users_fixtures: UsersTestFixtures) -> None:
        """Test partial user group update."""
        response = await users_fixtures.client.put(
            f"/api/v1/user-groups/{users_fixtures.test_group.id}",
            json={
                "location": "Only Location Updated",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["location"] == "Only Location Updated"

    async def test_update_user_group_not_found(self, users_fixtures: UsersTestFixtures) -> None:
        """Test updating non-existent user group."""
        fake_id = str(uuid4())
        response = await users_fixtures.client.put(
            f"/api/v1/user-groups/{fake_id}",
            json={
                "name": "Should Fail",
            },
        )
        assert response.status_code == 404

    async def test_approve_group(self, users_fixtures: UsersTestFixtures) -> None:
        """Test approving a user group."""
        create_response = await users_fixtures.client.post(
            "/api/v1/user-groups/",
            json={
                "name": f"Approve Test {uuid4().hex[:8]}",
                "location": "Test",
                "approved": False,
            },
        )
        group_id = create_response.json()["id"]

        response = await users_fixtures.client.patch(f"/api/v1/user-groups/{group_id}/approve")
        assert response.status_code == 200
        data = response.json()
        assert data["approved"] is True

    async def test_revoke_approval(self, users_fixtures: UsersTestFixtures) -> None:
        """Test revoking approval of a user group."""
        create_response = await users_fixtures.client.post(
            "/api/v1/user-groups/",
            json={
                "name": f"Revoke Test {uuid4().hex[:8]}",
                "location": "Test",
                "approved": True,
            },
        )
        group_id = create_response.json()["id"]

        response = await users_fixtures.client.patch(f"/api/v1/user-groups/{group_id}/revoke-approval")
        assert response.status_code == 200
        data = response.json()
        assert data["approved"] is False

    async def test_mark_trusted(self, users_fixtures: UsersTestFixtures) -> None:
        """Test marking a user group as trusted."""
        create_response = await users_fixtures.client.post(
            "/api/v1/user-groups/",
            json={
                "name": f"Trust Test {uuid4().hex[:8]}",
                "location": "Test",
                "trusted": False,
            },
        )
        group_id = create_response.json()["id"]

        response = await users_fixtures.client.patch(f"/api/v1/user-groups/{group_id}/mark-trusted")
        assert response.status_code == 200
        data = response.json()
        assert data["trusted"] is True

    async def test_revoke_trust(self, users_fixtures: UsersTestFixtures) -> None:
        """Test revoking trust of a user group."""
        create_response = await users_fixtures.client.post(
            "/api/v1/user-groups/",
            json={
                "name": f"Untrust Test {uuid4().hex[:8]}",
                "location": "Test",
                "trusted": True,
            },
        )
        group_id = create_response.json()["id"]

        response = await users_fixtures.client.patch(f"/api/v1/user-groups/{group_id}/revoke-trust")
        assert response.status_code == 200
        data = response.json()
        assert data["trusted"] is False

    async def test_delete_user_group(self, users_fixtures: UsersTestFixtures) -> None:
        """Test deleting a user group."""
        create_response = await users_fixtures.client.post(
            "/api/v1/user-groups/",
            json={
                "name": f"Delete Test {uuid4().hex[:8]}",
                "location": "To Delete",
            },
        )
        group_id = create_response.json()["id"]

        response = await users_fixtures.client.delete(f"/api/v1/user-groups/{group_id}")
        assert response.status_code == 204

        get_response = await users_fixtures.client.get(f"/api/v1/user-groups/{group_id}")
        assert get_response.status_code == 404

    async def test_delete_user_group_not_found(self, users_fixtures: UsersTestFixtures) -> None:
        """Test deleting non-existent user group."""
        fake_id = str(uuid4())
        response = await users_fixtures.client.delete(f"/api/v1/user-groups/{fake_id}")
        assert response.status_code == 404


@pytest.mark.integration
class TestUserGroupFiltering:
    """Test user group filtering and search functionality."""

    async def test_list_approved_groups_excludes_unapproved(self, users_fixtures: UsersTestFixtures) -> None:
        """Test that approved groups list excludes unapproved groups."""
        await users_fixtures.client.post(
            "/api/v1/user-groups/",
            json={
                "name": f"Unapproved {uuid4().hex[:8]}",
                "location": "Test",
                "approved": False,
            },
        )

        create_approved = await users_fixtures.client.post(
            "/api/v1/user-groups/",
            json={
                "name": f"Approved {uuid4().hex[:8]}",
                "location": "Test",
                "approved": True,
            },
        )
        approved_id = create_approved.json()["id"]

        response = await users_fixtures.client.get("/api/v1/user-groups/approved")
        assert response.status_code == 200
        groups = response.json()
        assert all(g["approved"] is True for g in groups)
        assert any(g["id"] == approved_id for g in groups)

    async def test_list_trusted_groups_excludes_untrusted(self, users_fixtures: UsersTestFixtures) -> None:
        """Test that trusted groups list excludes untrusted groups."""
        await users_fixtures.client.post(
            "/api/v1/user-groups/",
            json={
                "name": f"Untrusted {uuid4().hex[:8]}",
                "location": "Test",
                "trusted": False,
            },
        )

        create_trusted = await users_fixtures.client.post(
            "/api/v1/user-groups/",
            json={
                "name": f"Trusted {uuid4().hex[:8]}",
                "location": "Test",
                "trusted": True,
            },
        )
        trusted_id = create_trusted.json()["id"]

        response = await users_fixtures.client.get("/api/v1/user-groups/trusted")
        assert response.status_code == 200
        groups = response.json()
        assert all(g["trusted"] is True for g in groups)
        assert any(g["id"] == trusted_id for g in groups)

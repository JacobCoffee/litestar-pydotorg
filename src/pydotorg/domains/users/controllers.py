"""User domain API controllers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, delete, get, patch, post, put
from litestar.params import Parameter

from pydotorg.domains.users import urls
from pydotorg.domains.users.schemas import (
    MembershipCreate,
    MembershipRead,
    MembershipUpdate,
    UserCreate,
    UserGroupCreate,
    UserGroupRead,
    UserGroupUpdate,
    UserPublic,
    UserRead,
    UserUpdate,
)
from pydotorg.domains.users.services import MembershipService, UserGroupService, UserService


class UserController(Controller):
    """Controller for User CRUD operations."""

    path = urls.USERS
    tags = ["Users"]

    @get("/")
    async def list_users(
        self,
        user_service: UserService,
        limit_offset: LimitOffset,
    ) -> list[UserPublic]:
        """List all users with pagination."""
        users, _total = await user_service.list_and_count(limit_offset)
        return [UserPublic.model_validate(user) for user in users]

    @get("/{user_id:uuid}")
    async def get_user(
        self,
        user_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID")],
    ) -> UserRead:
        """Get a user by ID."""
        user = await user_service.get(user_id)
        return UserRead.model_validate(user)

    @get("/username/{username:str}")
    async def get_user_by_username(
        self,
        user_service: UserService,
        username: Annotated[str, Parameter(title="Username", description="The username")],
    ) -> UserPublic:
        """Get a user by username."""
        user = await user_service.get_by_username(username)
        if not user:
            msg = f"User with username {username} not found"
            raise ValueError(msg)
        return UserPublic.model_validate(user)

    @get("/email/{email:str}")
    async def get_user_by_email(
        self,
        user_service: UserService,
        email: Annotated[str, Parameter(title="Email", description="The email address")],
    ) -> UserRead:
        """Get a user by email."""
        user = await user_service.get_by_email(email)
        if not user:
            msg = f"User with email {email} not found"
            raise ValueError(msg)
        return UserRead.model_validate(user)

    @post("/")
    async def create_user(
        self,
        user_service: UserService,
        data: UserCreate,
    ) -> UserRead:
        """Create a new user."""
        user = await user_service.create_user(data)
        return UserRead.model_validate(user)

    @put("/{user_id:uuid}")
    async def update_user(
        self,
        user_service: UserService,
        data: UserUpdate,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID")],
    ) -> UserRead:
        """Update a user."""
        update_data = data.model_dump(exclude_unset=True)
        user = await user_service.update(user_id, update_data)
        return UserRead.model_validate(user)

    @patch("/{user_id:uuid}/deactivate")
    async def deactivate_user(
        self,
        user_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID")],
    ) -> UserRead:
        """Deactivate a user account."""
        user = await user_service.deactivate(user_id)
        return UserRead.model_validate(user)

    @patch("/{user_id:uuid}/reactivate")
    async def reactivate_user(
        self,
        user_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID")],
    ) -> UserRead:
        """Reactivate a user account."""
        user = await user_service.reactivate(user_id)
        return UserRead.model_validate(user)

    @delete("/{user_id:uuid}")
    async def delete_user(
        self,
        user_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID")],
    ) -> None:
        """Delete a user."""
        await user_service.delete(user_id)


class MembershipController(Controller):
    """Controller for Membership CRUD operations."""

    path = urls.MEMBERSHIPS
    tags = ["Users"]

    @get("/")
    async def list_memberships(
        self,
        membership_service: MembershipService,
        limit_offset: LimitOffset,
    ) -> list[MembershipRead]:
        """List all memberships with pagination."""
        memberships, _total = await membership_service.list_and_count(limit_offset)
        return [MembershipRead.model_validate(m) for m in memberships]

    @get("/{membership_id:uuid}")
    async def get_membership(
        self,
        membership_service: MembershipService,
        membership_id: Annotated[UUID, Parameter(title="Membership ID", description="The membership ID")],
    ) -> MembershipRead:
        """Get a membership by ID."""
        membership = await membership_service.get(membership_id)
        return MembershipRead.model_validate(membership)

    @get("/user/{user_id:uuid}")
    async def get_membership_by_user(
        self,
        membership_service: MembershipService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID")],
    ) -> MembershipRead:
        """Get a membership by user ID."""
        membership = await membership_service.get_by_user_id(user_id)
        if not membership:
            msg = f"Membership for user {user_id} not found"
            raise ValueError(msg)
        return MembershipRead.model_validate(membership)

    @post("/")
    async def create_membership(
        self,
        membership_service: MembershipService,
        data: MembershipCreate,
    ) -> MembershipRead:
        """Create a new membership."""
        membership_data = data.model_dump()
        user_id = membership_data.pop("user_id")
        membership = await membership_service.create_for_user(user_id, membership_data)
        return MembershipRead.model_validate(membership)

    @put("/{membership_id:uuid}")
    async def update_membership(
        self,
        membership_service: MembershipService,
        data: MembershipUpdate,
        membership_id: Annotated[UUID, Parameter(title="Membership ID", description="The membership ID")],
    ) -> MembershipRead:
        """Update a membership."""
        update_data = data.model_dump(exclude_unset=True)
        membership = await membership_service.update(membership_id, update_data)
        return MembershipRead.model_validate(membership)

    @delete("/{membership_id:uuid}")
    async def delete_membership(
        self,
        membership_service: MembershipService,
        membership_id: Annotated[UUID, Parameter(title="Membership ID", description="The membership ID")],
    ) -> None:
        """Delete a membership."""
        await membership_service.delete(membership_id)


class UserGroupController(Controller):
    """Controller for UserGroup CRUD operations."""

    path = urls.USER_GROUPS
    tags = ["Users"]

    @get("/")
    async def list_user_groups(
        self,
        user_group_service: UserGroupService,
        limit_offset: LimitOffset,
    ) -> list[UserGroupRead]:
        """List all user groups with pagination."""
        groups, _total = await user_group_service.list_and_count(limit_offset)
        return [UserGroupRead.model_validate(g) for g in groups]

    @get("/approved")
    async def list_approved_groups(
        self,
        user_group_service: UserGroupService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[UserGroupRead]:
        """List approved user groups."""
        groups = await user_group_service.list_approved(limit=limit, offset=offset)
        return [UserGroupRead.model_validate(g) for g in groups]

    @get("/trusted")
    async def list_trusted_groups(
        self,
        user_group_service: UserGroupService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[UserGroupRead]:
        """List trusted user groups."""
        groups = await user_group_service.list_trusted(limit=limit, offset=offset)
        return [UserGroupRead.model_validate(g) for g in groups]

    @get("/{group_id:uuid}")
    async def get_user_group(
        self,
        user_group_service: UserGroupService,
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> UserGroupRead:
        """Get a user group by ID."""
        group = await user_group_service.get(group_id)
        return UserGroupRead.model_validate(group)

    @post("/")
    async def create_user_group(
        self,
        user_group_service: UserGroupService,
        data: UserGroupCreate,
    ) -> UserGroupRead:
        """Create a new user group."""
        group = await user_group_service.create(data.model_dump())
        return UserGroupRead.model_validate(group)

    @put("/{group_id:uuid}")
    async def update_user_group(
        self,
        user_group_service: UserGroupService,
        data: UserGroupUpdate,
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> UserGroupRead:
        """Update a user group."""
        update_data = data.model_dump(exclude_unset=True)
        group = await user_group_service.update(group_id, update_data)
        return UserGroupRead.model_validate(group)

    @patch("/{group_id:uuid}/approve")
    async def approve_group(
        self,
        user_group_service: UserGroupService,
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> UserGroupRead:
        """Approve a user group."""
        group = await user_group_service.approve(group_id)
        return UserGroupRead.model_validate(group)

    @patch("/{group_id:uuid}/revoke-approval")
    async def revoke_approval(
        self,
        user_group_service: UserGroupService,
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> UserGroupRead:
        """Revoke approval of a user group."""
        group = await user_group_service.revoke_approval(group_id)
        return UserGroupRead.model_validate(group)

    @patch("/{group_id:uuid}/mark-trusted")
    async def mark_trusted(
        self,
        user_group_service: UserGroupService,
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> UserGroupRead:
        """Mark a user group as trusted."""
        group = await user_group_service.mark_trusted(group_id)
        return UserGroupRead.model_validate(group)

    @patch("/{group_id:uuid}/revoke-trust")
    async def revoke_trust(
        self,
        user_group_service: UserGroupService,
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> UserGroupRead:
        """Revoke trust of a user group."""
        group = await user_group_service.revoke_trust(group_id)
        return UserGroupRead.model_validate(group)

    @delete("/{group_id:uuid}")
    async def delete_user_group(
        self,
        user_group_service: UserGroupService,
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> None:
        """Delete a user group."""
        await user_group_service.delete(group_id)

"""User domain API controllers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, Request, delete, get, patch, post, put
from litestar.exceptions import NotFoundException
from litestar.openapi import ResponseSpec
from litestar.params import Body, Parameter

from pydotorg.core.auth.guards import require_authenticated
from pydotorg.domains.users import urls
from pydotorg.domains.users.models import User
from pydotorg.domains.users.schemas import (
    APIKeyCreate,
    APIKeyCreated,
    APIKeyRead,
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
from pydotorg.domains.users.services import APIKeyService, MembershipService, UserGroupService, UserService


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
        """List all users with pagination.

        Retrieves a paginated list of users from the database. Returns public user
        information only, excluding sensitive fields like email addresses.

        Args:
            user_service: Service for user database operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of public user profiles with basic information.
        """
        users, _total = await user_service.list_and_count(limit_offset)
        return [UserPublic.model_validate(user) for user in users]

    @get(
        "/{user_id:uuid}",
        responses={
            404: ResponseSpec(None, description="User not found"),
        },
    )
    async def get_user(
        self,
        user_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID")],
    ) -> UserRead:
        """Retrieve a specific user by their unique identifier.

        Fetches complete user information from the database including all profile
        fields. This endpoint returns full user details suitable for administrative
        or authenticated contexts.

        Args:
            user_service: Service for user database operations.
            user_id: The unique UUID identifier of the user.

        Returns:
            Complete user details including all profile fields.

        Raises:
            NotFoundException: If no user with the given ID exists.
        """
        user = await user_service.get(user_id)
        return UserRead.model_validate(user)

    @get(
        "/username/{username:str}",
        responses={
            404: ResponseSpec(None, description="User not found"),
        },
    )
    async def get_user_by_username(
        self,
        user_service: UserService,
        username: Annotated[str, Parameter(title="Username", description="The username")],
    ) -> UserPublic:
        """Look up a user by their username.

        Searches for a user with the specified username and returns their public
        profile. Usernames are case-sensitive and must match exactly.

        Args:
            user_service: Service for user database operations.
            username: The exact username to search for.

        Returns:
            Public profile information for the matching user.

        Raises:
            ValueError: If no user with the given username exists.
        """
        user = await user_service.get_by_username(username)
        if not user:
            msg = f"User with username {username} not found"
            raise ValueError(msg)
        return UserPublic.model_validate(user)

    @get(
        "/email/{email:str}",
        responses={
            404: ResponseSpec(None, description="User not found"),
        },
    )
    async def get_user_by_email(
        self,
        user_service: UserService,
        email: Annotated[str, Parameter(title="Email", description="The email address")],
    ) -> UserRead:
        """Look up a user by their email address.

        Searches for a user with the specified email address and returns their
        full profile. Email matching is case-insensitive. This endpoint returns
        full user details and should be restricted to authenticated contexts.

        Args:
            user_service: Service for user database operations.
            email: The email address to search for.

        Returns:
            Complete user details for the matching user.

        Raises:
            ValueError: If no user with the given email exists.
        """
        user = await user_service.get_by_email(email)
        if not user:
            msg = f"User with email {email} not found"
            raise ValueError(msg)
        return UserRead.model_validate(user)

    @post(
        "/",
        responses={
            422: ResponseSpec(None, description="Validation error"),
        },
    )
    async def create_user(
        self,
        user_service: UserService,
        data: Annotated[UserCreate, Body(title="User", description="User to create")],
    ) -> UserRead:
        """Create a new user account.

        Registers a new user in the system with the provided profile information.
        The password will be securely hashed before storage. Username and email
        must be unique across all users.

        Args:
            user_service: Service for user database operations.
            data: User creation payload containing required profile fields.

        Returns:
            The newly created user with all profile fields.

        Raises:
            ValidationError: If required fields are missing or invalid.
            ConflictError: If username or email already exists.
        """
        user = await user_service.create_user(data)
        return UserRead.model_validate(user)

    @put(
        "/{user_id:uuid}",
        responses={
            404: ResponseSpec(None, description="User not found"),
            422: ResponseSpec(None, description="Validation error"),
        },
    )
    async def update_user(
        self,
        user_service: UserService,
        data: Annotated[UserUpdate, Body(title="User", description="User data to update")],
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID")],
    ) -> UserRead:
        """Update an existing user's profile.

        Modifies user profile fields with the provided values. Only fields
        included in the request body will be updated; omitted fields remain
        unchanged. Password updates trigger re-hashing.

        Args:
            user_service: Service for user database operations.
            data: Partial user update payload with fields to modify.
            user_id: The unique UUID identifier of the user to update.

        Returns:
            The updated user with all current profile fields.

        Raises:
            NotFoundException: If no user with the given ID exists.
            ConflictError: If updated username or email conflicts with another user.
        """
        update_data = data.model_dump(exclude_unset=True)
        user = await user_service.update(user_id, update_data)
        return UserRead.model_validate(user)

    @patch(
        "/{user_id:uuid}/deactivate",
        responses={
            404: ResponseSpec(None, description="User not found"),
        },
    )
    async def deactivate_user(
        self,
        user_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID")],
    ) -> UserRead:
        """Deactivate a user account.

        Marks a user account as inactive, preventing login and access to
        authenticated features. The user data is preserved and can be
        reactivated later. This is preferred over deletion for audit purposes.

        Args:
            user_service: Service for user database operations.
            user_id: The unique UUID identifier of the user to deactivate.

        Returns:
            The deactivated user with updated status.

        Raises:
            NotFoundException: If no user with the given ID exists.
        """
        user = await user_service.deactivate(user_id)
        return UserRead.model_validate(user)

    @patch(
        "/{user_id:uuid}/reactivate",
        responses={
            404: ResponseSpec(None, description="User not found"),
        },
    )
    async def reactivate_user(
        self,
        user_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID")],
    ) -> UserRead:
        """Reactivate a previously deactivated user account.

        Restores access to a deactivated user account, allowing the user to
        log in and use authenticated features again. All previous user data
        and associations are preserved.

        Args:
            user_service: Service for user database operations.
            user_id: The unique UUID identifier of the user to reactivate.

        Returns:
            The reactivated user with updated status.

        Raises:
            NotFoundException: If no user with the given ID exists.
        """
        user = await user_service.reactivate(user_id)
        return UserRead.model_validate(user)

    @delete(
        "/{user_id:uuid}",
        responses={
            404: ResponseSpec(None, description="User not found"),
        },
    )
    async def delete_user(
        self,
        user_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID")],
    ) -> None:
        """Permanently delete a user account.

        Removes a user and all associated data from the system. This action
        is irreversible. Consider using deactivation instead for audit trail
        preservation.

        Args:
            user_service: Service for user database operations.
            user_id: The unique UUID identifier of the user to delete.

        Raises:
            NotFoundException: If no user with the given ID exists.
        """
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
        """List all memberships with pagination.

        Retrieves a paginated list of PSF memberships from the database.
        Includes membership type, status, and associated user information.

        Args:
            membership_service: Service for membership database operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of membership records with user associations.
        """
        memberships, _total = await membership_service.list_and_count(limit_offset)
        return [MembershipRead.model_validate(m) for m in memberships]

    @get(
        "/{membership_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Membership not found"),
        },
    )
    async def get_membership(
        self,
        membership_service: MembershipService,
        membership_id: Annotated[UUID, Parameter(title="Membership ID", description="The membership ID")],
    ) -> MembershipRead:
        """Retrieve a specific membership by its unique identifier.

        Fetches complete membership information including type, status,
        dates, and associated user details.

        Args:
            membership_service: Service for membership database operations.
            membership_id: The unique UUID identifier of the membership.

        Returns:
            Complete membership details including user association.

        Raises:
            NotFoundException: If no membership with the given ID exists.
        """
        membership = await membership_service.get(membership_id)
        return MembershipRead.model_validate(membership)

    @get(
        "/user/{user_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Membership not found"),
        },
    )
    async def get_membership_by_user(
        self,
        membership_service: MembershipService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user ID")],
    ) -> MembershipRead:
        """Look up a membership by the associated user ID.

        Retrieves the membership record for a specific user. Each user can
        have at most one active membership at a time.

        Args:
            membership_service: Service for membership database operations.
            user_id: The unique UUID identifier of the user.

        Returns:
            Membership details for the specified user.

        Raises:
            ValueError: If no membership exists for the given user.
        """
        membership = await membership_service.get_by_user_id(user_id)
        if not membership:
            msg = f"Membership for user {user_id} not found"
            raise ValueError(msg)
        return MembershipRead.model_validate(membership)

    @post("/")
    async def create_membership(
        self,
        membership_service: MembershipService,
        data: Annotated[MembershipCreate, Body(title="Membership", description="Membership to create")],
    ) -> MembershipRead:
        """Create a new PSF membership for a user.

        Associates a new membership record with an existing user account.
        The membership type and initial status are set based on the provided data.

        Args:
            membership_service: Service for membership database operations.
            data: Membership creation payload with user ID and membership details.

        Returns:
            The newly created membership record.

        Raises:
            NotFoundException: If the specified user does not exist.
            ConflictError: If the user already has an active membership.
        """
        membership_data = data.model_dump()
        user_id = membership_data.pop("user_id")
        membership = await membership_service.create_for_user(user_id, membership_data)
        return MembershipRead.model_validate(membership)

    @put(
        "/{membership_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Membership not found"),
            422: ResponseSpec(None, description="Validation error"),
        },
    )
    async def update_membership(
        self,
        membership_service: MembershipService,
        data: Annotated[MembershipUpdate, Body(title="Membership", description="Membership data to update")],
        membership_id: Annotated[UUID, Parameter(title="Membership ID", description="The membership ID")],
    ) -> MembershipRead:
        """Update an existing membership record.

        Modifies membership fields with the provided values. Can be used to
        change membership type, update status, or modify dates.

        Args:
            membership_service: Service for membership database operations.
            data: Partial membership update payload with fields to modify.
            membership_id: The unique UUID identifier of the membership to update.

        Returns:
            The updated membership with all current fields.

        Raises:
            NotFoundException: If no membership with the given ID exists.
        """
        update_data = data.model_dump(exclude_unset=True)
        membership = await membership_service.update(membership_id, update_data)
        return MembershipRead.model_validate(membership)

    @delete(
        "/{membership_id:uuid}",
        responses={
            404: ResponseSpec(None, description="Membership not found"),
        },
    )
    async def delete_membership(
        self,
        membership_service: MembershipService,
        membership_id: Annotated[UUID, Parameter(title="Membership ID", description="The membership ID")],
    ) -> None:
        """Delete a membership record.

        Permanently removes a membership from the system. The associated user
        account remains intact. This action is irreversible.

        Args:
            membership_service: Service for membership database operations.
            membership_id: The unique UUID identifier of the membership to delete.

        Raises:
            NotFoundException: If no membership with the given ID exists.
        """
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
        """List all user groups with pagination.

        Retrieves a paginated list of user groups including both approved
        and pending groups. Groups organize users for permissions and features.

        Args:
            user_group_service: Service for user group database operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of user groups with their metadata and status.
        """
        groups, _total = await user_group_service.list_and_count(limit_offset)
        return [UserGroupRead.model_validate(g) for g in groups]

    @get("/approved")
    async def list_approved_groups(
        self,
        user_group_service: UserGroupService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[UserGroupRead]:
        """List only approved user groups.

        Retrieves user groups that have been approved by administrators.
        Approved groups are visible to users and can be joined.

        Args:
            user_group_service: Service for user group database operations.
            limit: Maximum number of groups to return (1-1000).
            offset: Number of groups to skip for pagination.

        Returns:
            List of approved user groups.
        """
        groups = await user_group_service.list_approved(limit=limit, offset=offset)
        return [UserGroupRead.model_validate(g) for g in groups]

    @get("/trusted")
    async def list_trusted_groups(
        self,
        user_group_service: UserGroupService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[UserGroupRead]:
        """List only trusted user groups.

        Retrieves user groups marked as trusted. Trusted groups have elevated
        privileges and are typically official Python community organizations.

        Args:
            user_group_service: Service for user group database operations.
            limit: Maximum number of groups to return (1-1000).
            offset: Number of groups to skip for pagination.

        Returns:
            List of trusted user groups.
        """
        groups = await user_group_service.list_trusted(limit=limit, offset=offset)
        return [UserGroupRead.model_validate(g) for g in groups]

    @get(
        "/{group_id:uuid}",
        responses={
            404: ResponseSpec(None, description="User group not found"),
        },
    )
    async def get_user_group(
        self,
        user_group_service: UserGroupService,
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> UserGroupRead:
        """Retrieve a specific user group by its unique identifier.

        Fetches complete user group information including name, description,
        approval status, and trust level.

        Args:
            user_group_service: Service for user group database operations.
            group_id: The unique UUID identifier of the user group.

        Returns:
            Complete user group details.

        Raises:
            NotFoundException: If no user group with the given ID exists.
        """
        group = await user_group_service.get(group_id)
        return UserGroupRead.model_validate(group)

    @post("/")
    async def create_user_group(
        self,
        user_group_service: UserGroupService,
        data: Annotated[UserGroupCreate, Body(title="User Group", description="User group to create")],
    ) -> UserGroupRead:
        """Create a new user group.

        Creates a new user group in pending status. Groups must be approved
        by administrators before becoming visible to users.

        Args:
            user_group_service: Service for user group database operations.
            data: User group creation payload with name and description.

        Returns:
            The newly created user group in pending status.

        Raises:
            ConflictError: If a group with the same name already exists.
        """
        group = await user_group_service.create(data.model_dump())
        return UserGroupRead.model_validate(group)

    @put(
        "/{group_id:uuid}",
        responses={
            404: ResponseSpec(None, description="User group not found"),
            422: ResponseSpec(None, description="Validation error"),
        },
    )
    async def update_user_group(
        self,
        user_group_service: UserGroupService,
        data: Annotated[UserGroupUpdate, Body(title="User Group", description="User group data to update")],
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> UserGroupRead:
        """Update an existing user group.

        Modifies user group fields with the provided values. Can update
        name, description, and other metadata. Status changes should use
        dedicated endpoints.

        Args:
            user_group_service: Service for user group database operations.
            data: Partial user group update payload with fields to modify.
            group_id: The unique UUID identifier of the user group to update.

        Returns:
            The updated user group with all current fields.

        Raises:
            NotFoundException: If no user group with the given ID exists.
        """
        update_data = data.model_dump(exclude_unset=True)
        group = await user_group_service.update(group_id, update_data)
        return UserGroupRead.model_validate(group)

    @patch("/{group_id:uuid}/approve")
    async def approve_group(
        self,
        user_group_service: UserGroupService,
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> UserGroupRead:
        """Approve a pending user group.

        Marks a user group as approved, making it visible to users and
        allowing membership. This action requires administrator privileges.

        Args:
            user_group_service: Service for user group database operations.
            group_id: The unique UUID identifier of the user group to approve.

        Returns:
            The approved user group with updated status.

        Raises:
            NotFoundException: If no user group with the given ID exists.
        """
        group = await user_group_service.approve(group_id)
        return UserGroupRead.model_validate(group)

    @patch("/{group_id:uuid}/revoke-approval")
    async def revoke_approval(
        self,
        user_group_service: UserGroupService,
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> UserGroupRead:
        """Revoke approval of a user group.

        Removes approved status from a user group, hiding it from users
        and preventing new memberships. Existing members are not removed.

        Args:
            user_group_service: Service for user group database operations.
            group_id: The unique UUID identifier of the user group.

        Returns:
            The user group with revoked approval status.

        Raises:
            NotFoundException: If no user group with the given ID exists.
        """
        group = await user_group_service.revoke_approval(group_id)
        return UserGroupRead.model_validate(group)

    @patch("/{group_id:uuid}/mark-trusted")
    async def mark_trusted(
        self,
        user_group_service: UserGroupService,
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> UserGroupRead:
        """Mark a user group as trusted.

        Grants trusted status to a user group, providing elevated privileges.
        Trusted groups are typically official Python community organizations.

        Args:
            user_group_service: Service for user group database operations.
            group_id: The unique UUID identifier of the user group.

        Returns:
            The user group with trusted status enabled.

        Raises:
            NotFoundException: If no user group with the given ID exists.
        """
        group = await user_group_service.mark_trusted(group_id)
        return UserGroupRead.model_validate(group)

    @patch("/{group_id:uuid}/revoke-trust")
    async def revoke_trust(
        self,
        user_group_service: UserGroupService,
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> UserGroupRead:
        """Revoke trusted status from a user group.

        Removes trusted status from a user group, revoking elevated privileges.
        The group remains approved and visible to users.

        Args:
            user_group_service: Service for user group database operations.
            group_id: The unique UUID identifier of the user group.

        Returns:
            The user group with trusted status revoked.

        Raises:
            NotFoundException: If no user group with the given ID exists.
        """
        group = await user_group_service.revoke_trust(group_id)
        return UserGroupRead.model_validate(group)

    @delete(
        "/{group_id:uuid}",
        responses={
            404: ResponseSpec(None, description="User group not found"),
        },
    )
    async def delete_user_group(
        self,
        user_group_service: UserGroupService,
        group_id: Annotated[UUID, Parameter(title="Group ID", description="The user group ID")],
    ) -> None:
        """Permanently delete a user group.

        Removes a user group and all associated memberships from the system.
        This action is irreversible. Consider revoking approval instead.

        Args:
            user_group_service: Service for user group database operations.
            group_id: The unique UUID identifier of the user group to delete.

        Raises:
            NotFoundException: If no user group with the given ID exists.
        """
        await user_group_service.delete(group_id)


class APIKeyController(Controller):
    """Controller for API key management.

    API keys allow programmatic access to the API. Users can create multiple keys
    with optional expiration dates. Keys are shown only once at creation time.
    """

    path = urls.API_KEYS
    tags = ["API Keys"]
    guards = [require_authenticated]

    @get("/")
    async def list_api_keys(
        self,
        request: Request[User, str, dict],
        api_key_service: APIKeyService,
    ) -> list[APIKeyRead]:
        """List all API keys for the authenticated user.

        Returns all API keys (both active and revoked) for the current user.
        The actual key values are not returned; only metadata is shown.

        Args:
            request: The HTTP request with authenticated user.
            api_key_service: Service for API key operations.

        Returns:
            List of API keys with metadata.
        """
        keys = await api_key_service.list_by_user(request.user.id)
        return [APIKeyRead.model_validate(k) for k in keys]

    @get("/active")
    async def list_active_api_keys(
        self,
        request: Request[User, str, dict],
        api_key_service: APIKeyService,
    ) -> list[APIKeyRead]:
        """List only active API keys for the authenticated user.

        Returns API keys that are currently active and not expired.

        Args:
            request: The HTTP request with authenticated user.
            api_key_service: Service for API key operations.

        Returns:
            List of active API keys with metadata.
        """
        keys = await api_key_service.list_active_by_user(request.user.id)
        return [APIKeyRead.model_validate(k) for k in keys]

    @get(
        "/{key_id:uuid}",
        responses={
            404: ResponseSpec(None, description="API key not found"),
        },
    )
    async def get_api_key(
        self,
        request: Request[User, str, dict],
        api_key_service: APIKeyService,
        key_id: Annotated[UUID, Parameter(title="Key ID", description="The API key ID")],
    ) -> APIKeyRead:
        """Get a specific API key by ID.

        Returns metadata for the specified API key. The actual key value
        is not returned.

        Args:
            request: The HTTP request with authenticated user.
            api_key_service: Service for API key operations.
            key_id: The unique identifier of the API key.

        Returns:
            API key metadata.

        Raises:
            NotFoundException: If the key doesn't exist or belongs to another user.
        """
        key = await api_key_service.get(key_id)
        if key.user_id != request.user.id:
            raise NotFoundException("API key not found")
        return APIKeyRead.model_validate(key)

    @post("/")
    async def create_api_key(
        self,
        request: Request[User, str, dict],
        api_key_service: APIKeyService,
        data: Annotated[APIKeyCreate, Body(title="API Key", description="API key to create")],
    ) -> APIKeyCreated:
        """Create a new API key.

        Generates a new API key for the authenticated user. The full key value
        is returned ONLY in this response and cannot be retrieved later.
        Store it securely!

        Args:
            request: The HTTP request with authenticated user.
            api_key_service: Service for API key operations.
            data: API key creation payload with name and optional expiration.

        Returns:
            The created API key including the raw key value.
        """
        key, raw_key = await api_key_service.create_key(request.user.id, data)
        result = APIKeyCreated.model_validate(key)
        result.key = raw_key
        return result

    @patch(
        "/{key_id:uuid}/revoke",
        responses={
            404: ResponseSpec(None, description="API key not found"),
        },
    )
    async def revoke_api_key(
        self,
        request: Request[User, str, dict],
        api_key_service: APIKeyService,
        key_id: Annotated[UUID, Parameter(title="Key ID", description="The API key ID")],
    ) -> APIKeyRead:
        """Revoke an API key.

        Deactivates the specified API key. The key cannot be reactivated;
        create a new key if needed.

        Args:
            request: The HTTP request with authenticated user.
            api_key_service: Service for API key operations.
            key_id: The unique identifier of the API key to revoke.

        Returns:
            The revoked API key metadata.

        Raises:
            NotFoundException: If the key doesn't exist or belongs to another user.
        """
        key = await api_key_service.get(key_id)
        if key.user_id != request.user.id:
            raise NotFoundException("API key not found")
        revoked = await api_key_service.revoke(key_id)
        return APIKeyRead.model_validate(revoked)

    @delete(
        "/{key_id:uuid}",
        responses={
            404: ResponseSpec(None, description="API key not found"),
        },
    )
    async def delete_api_key(
        self,
        request: Request[User, str, dict],
        api_key_service: APIKeyService,
        key_id: Annotated[UUID, Parameter(title="Key ID", description="The API key ID")],
    ) -> None:
        """Delete an API key.

        Permanently removes an API key from the system. This action is irreversible.

        Args:
            request: The HTTP request with authenticated user.
            api_key_service: Service for API key operations.
            key_id: The unique identifier of the API key to delete.

        Raises:
            NotFoundException: If the key doesn't exist or belongs to another user.
        """
        key = await api_key_service.get(key_id)
        if key.user_id != request.user.id:
            raise NotFoundException("API key not found")
        await api_key_service.delete(key_id)

    @post("/revoke-all", status_code=200)
    async def revoke_all_api_keys(
        self,
        request: Request[User, str, dict],
        api_key_service: APIKeyService,
    ) -> dict[str, int]:
        """Revoke all API keys for the authenticated user.

        Deactivates all active API keys. This is useful when keys may have
        been compromised.

        Args:
            request: The HTTP request with authenticated user.
            api_key_service: Service for API key operations.

        Returns:
            Dictionary with count of revoked keys.
        """
        count = await api_key_service.revoke_all_for_user(request.user.id)
        return {"revoked": count}

"""Users domain - User management, memberships, and authentication."""

from pydotorg.domains.users import urls
from pydotorg.domains.users.api_keys import APIKey
from pydotorg.domains.users.controllers import (
    APIKeyController,
    MembershipController,
    UserController,
    UserGroupController,
)
from pydotorg.domains.users.dependencies import get_user_dependencies
from pydotorg.domains.users.models import (
    EmailPrivacy,
    Membership,
    MembershipType,
    SearchVisibility,
    User,
    UserGroup,
    UserGroupType,
)
from pydotorg.domains.users.repositories import (
    APIKeyRepository,
    MembershipRepository,
    UserGroupRepository,
    UserRepository,
)
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

__all__ = [
    "APIKey",
    "APIKeyController",
    "APIKeyCreate",
    "APIKeyCreated",
    "APIKeyRead",
    "APIKeyRepository",
    "APIKeyService",
    "EmailPrivacy",
    "Membership",
    "MembershipController",
    "MembershipCreate",
    "MembershipRead",
    "MembershipRepository",
    "MembershipService",
    "MembershipType",
    "MembershipUpdate",
    "SearchVisibility",
    "User",
    "UserController",
    "UserCreate",
    "UserGroup",
    "UserGroupController",
    "UserGroupCreate",
    "UserGroupRead",
    "UserGroupRepository",
    "UserGroupService",
    "UserGroupType",
    "UserGroupUpdate",
    "UserPublic",
    "UserRead",
    "UserRepository",
    "UserService",
    "UserUpdate",
    "get_user_dependencies",
    "urls",
]

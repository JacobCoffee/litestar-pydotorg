"""Users domain - User management, memberships, and authentication."""

from pydotorg.domains.users import urls
from pydotorg.domains.users.controllers import MembershipController, UserController, UserGroupController
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
from pydotorg.domains.users.repositories import MembershipRepository, UserGroupRepository, UserRepository
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

__all__ = [
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

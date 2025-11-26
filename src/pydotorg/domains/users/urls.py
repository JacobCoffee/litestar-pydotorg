"""Users domain URL constants."""

from typing import Final

USERS: Final[str] = "/api/v1/users"
USER_BY_ID: Final[str] = "/api/v1/users/{user_id:uuid}"
USER_BY_USERNAME: Final[str] = "/api/v1/users/username/{username:str}"
USER_BY_EMAIL: Final[str] = "/api/v1/users/email/{email:str}"
USER_DEACTIVATE: Final[str] = "/api/v1/users/{user_id:uuid}/deactivate"
USER_REACTIVATE: Final[str] = "/api/v1/users/{user_id:uuid}/reactivate"

MEMBERSHIPS: Final[str] = "/api/v1/memberships"
MEMBERSHIP_BY_ID: Final[str] = "/api/v1/memberships/{membership_id:uuid}"
MEMBERSHIP_BY_USER: Final[str] = "/api/v1/memberships/user/{user_id:uuid}"

USER_GROUPS: Final[str] = "/api/v1/user-groups"
USER_GROUP_BY_ID: Final[str] = "/api/v1/user-groups/{group_id:uuid}"
USER_GROUPS_APPROVED: Final[str] = "/api/v1/user-groups/approved"
USER_GROUPS_TRUSTED: Final[str] = "/api/v1/user-groups/trusted"
USER_GROUP_APPROVE: Final[str] = "/api/v1/user-groups/{group_id:uuid}/approve"
USER_GROUP_REVOKE_APPROVAL: Final[str] = "/api/v1/user-groups/{group_id:uuid}/revoke-approval"
USER_GROUP_MARK_TRUSTED: Final[str] = "/api/v1/user-groups/{group_id:uuid}/mark-trusted"
USER_GROUP_REVOKE_TRUST: Final[str] = "/api/v1/user-groups/{group_id:uuid}/revoke-trust"

AUTH_LOGIN: Final[str] = "/api/auth/login"
AUTH_REGISTER: Final[str] = "/api/auth/register"
AUTH_LOGOUT: Final[str] = "/api/auth/logout"
AUTH_REFRESH: Final[str] = "/api/auth/refresh"
AUTH_ME: Final[str] = "/api/auth/me"

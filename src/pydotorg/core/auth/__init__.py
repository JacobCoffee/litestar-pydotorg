"""Authentication and authorization module."""

from pydotorg.core.auth.guards import (
    require_admin,
    require_authenticated,
    require_higher_membership,
    require_membership,
    require_staff,
)
from pydotorg.core.auth.jwt import jwt_service
from pydotorg.core.auth.middleware import JWTAuthMiddleware
from pydotorg.core.auth.password import password_service
from pydotorg.core.auth.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from pydotorg.core.auth.session import SessionAuthMiddleware, SessionService, session_service

__all__ = [
    "JWTAuthMiddleware",
    "LoginRequest",
    "RefreshTokenRequest",
    "RegisterRequest",
    "SessionAuthMiddleware",
    "SessionService",
    "TokenResponse",
    "UserResponse",
    "jwt_service",
    "password_service",
    "require_admin",
    "require_authenticated",
    "require_higher_membership",
    "require_membership",
    "require_staff",
    "session_service",
]

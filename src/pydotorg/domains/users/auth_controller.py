"""Authentication endpoints controller."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from litestar import Controller, Request, Response, delete, get, post, put
from litestar.di import Provide
from litestar.exceptions import NotFoundException, PermissionDeniedException
from litestar.params import Parameter
from litestar.response import Redirect, Template
from sqlalchemy import select

from pydotorg.config import settings
from pydotorg.core.auth.guards import require_authenticated
from pydotorg.core.auth.jwt import jwt_service
from pydotorg.core.auth.oauth import get_oauth_service
from pydotorg.core.auth.password import password_service
from pydotorg.core.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ProfileUpdateRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendVerificationRequest,
    SettingsUpdateRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailResponse,
)
from pydotorg.core.auth.session import session_service
from pydotorg.core.logging import get_logger
from pydotorg.domains.users.models import EmailPrivacy, SearchVisibility, User
from pydotorg.lib.tasks import enqueue_task

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


async def get_current_user(request: Request) -> User:
    if not request.user:
        raise NotFoundException("User not found")
    return request.user


class AuthController(Controller):
    """Authentication API for user registration, login, and session management.

    Provides JWT-based authentication with access and refresh tokens, session-based
    authentication via cookies, OAuth integration (GitHub), and email verification.
    """

    path = "/api/auth"
    tags = ["Authentication"]
    dependencies = {"current_user": Provide(get_current_user)}

    @post("/register")
    async def register(
        self,
        data: RegisterRequest,
        db_session: AsyncSession,
    ) -> TokenResponse:
        """Register a new user account.

        Creates a new user with the provided credentials and sends a verification
        email. Returns JWT tokens for immediate authentication.

        Password Requirements:
        - Minimum 8 characters
        - At least one uppercase and lowercase letter
        - At least one digit
        - At least one special character

        Example:
            POST /api/auth/register
            {"username": "newuser", "email": "user@example.com",
             "password": "SecureP@ss123", "first_name": "John", "last_name": "Doe"}

        Returns:
            JWT access and refresh tokens with expiration info.

        Raises:
            PermissionDeniedException: If username/email exists or password is weak.
        """
        result = await db_session.execute(
            select(User).where((User.username == data.username) | (User.email == data.email))
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.username == data.username:
                raise PermissionDeniedException("Username already exists")
            raise PermissionDeniedException("Email already registered")

        is_valid, error_message = password_service.validate_password_strength(data.password)
        if not is_valid:
            raise PermissionDeniedException(error_message or "Password does not meet requirements")

        user = User(
            username=data.username,
            email=data.email,
            password_hash=password_service.hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            is_active=True,
            last_login=datetime.now(UTC),
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        verification_token = jwt_service.create_verification_token(user.id, user.email)
        verification_link = f"{settings.oauth_redirect_base_url}/verify-email/{verification_token}"

        await enqueue_task(
            "send_verification_email",
            to_email=user.email,
            username=user.username,
            verification_link=verification_link,
        )

        access_token = jwt_service.create_access_token(user.id)
        refresh_token = jwt_service.create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_expiration_minutes * 60,
        )

    @post("/login", status_code=200)
    async def login(
        self,
        data: LoginRequest,
        db_session: AsyncSession,
    ) -> TokenResponse:
        """Authenticate user with username and password.

        Validates credentials and returns JWT tokens for API authentication.
        Use the access_token in the Authorization header as: Bearer <token>

        Example:
            POST /api/auth/login
            {"username": "myuser", "password": "mypassword"}

        Returns:
            access_token: Short-lived token for API requests (default: 30 min)
            refresh_token: Long-lived token for refreshing access (default: 7 days)
            expires_in: Access token lifetime in seconds

        Raises:
            PermissionDeniedException: Invalid credentials or inactive account.
        """
        result = await db_session.execute(select(User).where(User.username == data.username))
        user = result.scalar_one_or_none()

        if not user:
            raise PermissionDeniedException("Invalid credentials")

        if user.oauth_provider:
            raise PermissionDeniedException(f"This account uses {user.oauth_provider} login")

        if not user.password_hash or not password_service.verify_password(data.password, user.password_hash):
            raise PermissionDeniedException("Invalid credentials")

        if not user.is_active:
            raise PermissionDeniedException("Account is inactive")

        user_id = user.id
        user.last_login = datetime.now(UTC)
        await db_session.commit()

        access_token = jwt_service.create_access_token(user_id)
        refresh_token = jwt_service.create_refresh_token(user_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_expiration_minutes * 60,
        )

    @post("/refresh", status_code=200)
    async def refresh_token(
        self,
        data: RefreshTokenRequest,
        db_session: AsyncSession,
    ) -> TokenResponse:
        """Refresh an expired access token using a valid refresh token.

        Exchange a refresh token for a new access/refresh token pair. Use this
        when the access token expires but the refresh token is still valid.

        Example:
            POST /api/auth/refresh
            {"refresh_token": "eyJhbGciOiJIUzI1NiIs..."}

        Returns:
            New access and refresh tokens with updated expiration.

        Raises:
            PermissionDeniedException: Invalid/expired refresh token or inactive user.
        """
        try:
            user_id = jwt_service.get_user_id_from_token(data.refresh_token, token_type="refresh")  # noqa: S106
        except ValueError as e:
            raise PermissionDeniedException("Invalid refresh token") from e

        result = await db_session.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
        user = result.scalar_one_or_none()

        if not user:
            raise PermissionDeniedException("User not found or inactive")

        access_token = jwt_service.create_access_token(user.id)
        refresh_token = jwt_service.create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_expiration_minutes * 60,
        )

    @post("/logout", guards=[require_authenticated], status_code=200)
    async def logout(self) -> dict[str, str]:
        """Logout the current user (JWT-based).

        Invalidates the current session. Requires a valid access token.
        Note: JWT tokens remain valid until expiration; client should discard them.

        Returns:
            Confirmation message.
        """
        return {"message": "Successfully logged out"}

    @post("/session/login")
    async def session_login(
        self,
        data: LoginRequest,
        db_session: AsyncSession,
    ) -> Response[dict[str, str]]:
        """Login using cookie-based sessions.

        Alternative to JWT authentication using HTTP-only session cookies.
        Preferred for browser-based applications for better security.

        Example:
            POST /api/auth/session/login
            {"username": "myuser", "password": "mypassword"}

        Returns:
            Success message with session cookie set in response headers.

        Raises:
            PermissionDeniedException: Invalid credentials or inactive account.
        """
        result = await db_session.execute(select(User).where(User.username == data.username))
        user = result.scalar_one_or_none()

        if not user:
            raise PermissionDeniedException("Invalid credentials")

        if user.oauth_provider:
            raise PermissionDeniedException(f"This account uses {user.oauth_provider} login")

        if not user.password_hash or not password_service.verify_password(data.password, user.password_hash):
            raise PermissionDeniedException("Invalid credentials")

        if not user.is_active:
            raise PermissionDeniedException("Account is inactive")

        user_id = user.id  # Capture before commit to avoid lazy load
        user.last_login = datetime.now(UTC)
        await db_session.commit()

        session_id = session_service.create_session(user_id)

        response = Response(
            content={"message": "Successfully logged in"},
            status_code=200,
        )

        response.set_cookie(
            key=settings.session_cookie_name,
            value=session_id,
            max_age=settings.session_expire_minutes * 60,
            httponly=True,
            secure=not settings.is_debug,
            samesite="lax",
            path="/",
        )

        return response

    @post("/session/logout", guards=[require_authenticated])
    async def session_logout(self, request: Request) -> Response[dict[str, str]]:
        """Logout and clear session cookie.

        Destroys the server-side session and clears the session cookie.

        Returns:
            Success message with cookie deletion header.
        """
        session_id = request.cookies.get(settings.session_cookie_name)

        if session_id:
            session_service.destroy_session(session_id)

        response = Response(
            content={"message": "Successfully logged out"},
            status_code=200,
        )

        response.delete_cookie(
            key=settings.session_cookie_name,
            path="/",
        )

        return response

    @post("/me", guards=[require_authenticated], status_code=200)
    async def get_me(self, current_user: User) -> UserResponse:
        """Get the currently authenticated user's profile.

        Returns the full profile of the authenticated user making the request.
        Requires valid authentication (JWT token or session cookie).

        Returns:
            Current user's profile including email, username, and account status.
        """
        return UserResponse.model_validate(current_user)

    @get("/oauth/{provider:str}")
    async def oauth_login(
        self,
        provider: str,
        request: Request,
    ) -> Redirect:
        """Initiate OAuth login flow.

        Redirects user to the OAuth provider's authorization page.
        Currently supported providers: github

        Example:
            GET /api/auth/oauth/github
            → Redirects to GitHub authorization page

        Args:
            provider: OAuth provider name (e.g., "github")

        Returns:
            Redirect to OAuth provider's authorization URL.

        Raises:
            PermissionDeniedException: Unknown provider.
        """
        oauth_service = get_oauth_service(settings)

        try:
            oauth_provider = oauth_service.get_provider(provider)
        except ValueError as e:
            raise PermissionDeniedException(str(e)) from e

        state = secrets.token_urlsafe(32)
        request.set_session({"oauth_state": state, "oauth_provider": provider})

        redirect_uri = f"{settings.oauth_redirect_base_url}/api/auth/oauth/{provider}/callback"
        auth_url = oauth_provider.get_authorization_url(redirect_uri, state)

        return Redirect(path=auth_url)

    @get("/oauth/{provider:str}/callback")
    async def oauth_callback(
        self,
        provider: str,
        request: Request,
        db_session: AsyncSession,
        code: str = Parameter(query="code"),
        oauth_state: str = Parameter(query="state"),
    ) -> Response[TokenResponse]:
        """Handle OAuth callback from provider.

        Processes the authorization code from the OAuth provider, exchanges it
        for tokens, and creates or links a user account. Returns JWT tokens.

        This endpoint is called by the OAuth provider after user authorization.
        New users are automatically registered; existing users are logged in.

        Args:
            provider: OAuth provider name
            code: Authorization code from OAuth provider
            oauth_state: State parameter for CSRF protection

        Returns:
            JWT access and refresh tokens.

        Raises:
            PermissionDeniedException: Invalid state, provider, or auth failure.
        """
        session_state = request.session.get("oauth_state")
        session_provider = request.session.get("oauth_provider")

        if not session_state or session_state != oauth_state:
            raise PermissionDeniedException("Invalid OAuth state")

        if session_provider != provider:
            raise PermissionDeniedException("OAuth provider mismatch")

        request.clear_session()

        oauth_service = get_oauth_service(settings)

        try:
            oauth_provider = oauth_service.get_provider(provider)
        except ValueError as e:
            raise PermissionDeniedException(str(e)) from e

        redirect_uri = f"{settings.oauth_redirect_base_url}/api/auth/oauth/{provider}/callback"

        try:
            token_data = await oauth_provider.exchange_code_for_token(code, redirect_uri)
            access_token = token_data.get("access_token")

            if not access_token:
                raise PermissionDeniedException("Failed to obtain access token")

            user_info = await oauth_provider.get_user_info(access_token)

        except Exception as e:
            raise PermissionDeniedException(f"OAuth authentication failed: {e!s}") from e

        result = await db_session.execute(
            select(User).where((User.oauth_provider == user_info.provider) & (User.oauth_id == user_info.oauth_id))
        )
        user = result.scalar_one_or_none()

        if not user:
            email_result = await db_session.execute(select(User).where(User.email == user_info.email))
            user = email_result.scalar_one_or_none()

            if user:
                if user.oauth_provider:
                    raise PermissionDeniedException(f"Email already registered with {user.oauth_provider}")

                user.oauth_provider = user_info.provider
                user.oauth_id = user_info.oauth_id
                user.email_verified = user_info.email_verified
            else:
                username = user_info.username
                username_check = await db_session.execute(select(User).where(User.username == username))
                if username_check.scalar_one_or_none():
                    username = f"{username}_{secrets.token_hex(4)}"

                user = User(
                    username=username,
                    email=user_info.email,
                    password_hash=None,
                    first_name=user_info.first_name,
                    last_name=user_info.last_name,
                    oauth_provider=user_info.provider,
                    oauth_id=user_info.oauth_id,
                    email_verified=user_info.email_verified,
                    is_active=True,
                    last_login=datetime.now(UTC),
                )
                db_session.add(user)
        else:
            user.last_login = datetime.now(UTC)

        await db_session.commit()
        await db_session.refresh(user)

        jwt_access_token = jwt_service.create_access_token(user.id)
        jwt_refresh_token = jwt_service.create_refresh_token(user.id)

        return Response(
            content=TokenResponse(
                access_token=jwt_access_token,
                refresh_token=jwt_refresh_token,
                expires_in=settings.jwt_expiration_minutes * 60,
            )
        )

    @post("/send-verification")
    async def send_verification(
        self,
        data: SendVerificationRequest,
        db_session: AsyncSession,
    ) -> VerifyEmailResponse:
        """Send email verification link to a user.

        Generates a verification token and sends an email with a verification
        link. Use this for users who registered but haven't verified their email.

        Example:
            POST /api/auth/send-verification
            {"email": "user@example.com"}

        Returns:
            Confirmation message.

        Raises:
            NotFoundException: User not found.
        """
        result = await db_session.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        if user.email_verified:
            return VerifyEmailResponse(message="Email already verified")

        verification_token = jwt_service.create_verification_token(user.id, user.email)
        verification_link = f"{settings.oauth_redirect_base_url}/verify-email/{verification_token}"

        await enqueue_task(
            "send_verification_email",
            to_email=user.email,
            username=user.username,
            verification_link=verification_link,
        )

        return VerifyEmailResponse(message="Verification email sent")

    @get("/verify-email/{token:str}")
    async def verify_email(
        self,
        token: str,
        db_session: AsyncSession,
    ) -> VerifyEmailResponse:
        """Verify user's email address using a verification token.

        Validates the token from the verification email and marks the user's
        email as verified.

        Args:
            token: JWT verification token from the email link.

        Returns:
            Confirmation of email verification.

        Raises:
            PermissionDeniedException: Invalid or expired token.
            NotFoundException: User not found.
        """
        try:
            payload = jwt_service.decode_token(token)
            jwt_service.verify_token_type(payload, "verify_email")

            user_id_str = payload.get("sub")
            email = payload.get("email")

            if not user_id_str or not email:
                raise PermissionDeniedException("Invalid verification token")

            user_id = UUID(user_id_str)

        except ValueError as e:
            raise PermissionDeniedException("Invalid or expired verification token") from e

        result = await db_session.execute(select(User).where(User.id == user_id, User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        if user.email_verified:
            return VerifyEmailResponse(message="Email already verified")

        user.email_verified = True
        await db_session.commit()

        return VerifyEmailResponse(message="Email verified successfully")

    @post("/resend-verification", guards=[require_authenticated])
    async def resend_verification(
        self,
        current_user: User,
    ) -> VerifyEmailResponse:
        """Resend verification email to the authenticated user.

        Sends a new verification email to the currently logged-in user.
        Requires authentication.

        Returns:
            Confirmation that email was sent.
        """
        if current_user.email_verified:
            return VerifyEmailResponse(message="Email already verified")

        verification_token = jwt_service.create_verification_token(current_user.id, current_user.email)
        verification_link = f"{settings.oauth_redirect_base_url}/verify-email/{verification_token}"

        await enqueue_task(
            "send_verification_email",
            to_email=current_user.email,
            username=current_user.username,
            verification_link=verification_link,
        )

        return VerifyEmailResponse(message="Verification email sent")

    @post("/forgot-password")
    async def forgot_password(
        self,
        data: ForgotPasswordRequest,
        db_session: AsyncSession,
    ) -> VerifyEmailResponse:
        """Request a password reset email.

        Sends a password reset link if the email exists and is not an OAuth account.
        Always returns the same message for security (prevents email enumeration).

        Example:
            POST /api/auth/forgot-password
            {"email": "user@example.com"}

        Returns:
            Generic confirmation message regardless of email existence.
        """
        result = await db_session.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user:
            return VerifyEmailResponse(
                message="If an account exists with this email, you will receive a password reset link"
            )

        if user.oauth_provider:
            return VerifyEmailResponse(
                message="If an account exists with this email, you will receive a password reset link"
            )

        reset_token = jwt_service.create_password_reset_token(user.id, user.email)
        reset_link = f"{settings.oauth_redirect_base_url}/auth/reset-password/{reset_token}"

        await enqueue_task(
            "send_password_reset_email",
            to_email=user.email,
            username=user.username,
            reset_link=reset_link,
        )

        return VerifyEmailResponse(
            message="If an account exists with this email, you will receive a password reset link"
        )

    @post("/reset-password")
    async def reset_password(
        self,
        data: ResetPasswordRequest,
        db_session: AsyncSession,
    ) -> VerifyEmailResponse:
        """Reset password using a reset token.

        Validates the reset token from the forgot-password email and sets
        a new password. Password must meet strength requirements.

        Example:
            POST /api/auth/reset-password
            {"token": "eyJhbGciOiJIUzI1NiIs...", "new_password": "NewSecureP@ss123"}

        Returns:
            Confirmation of password reset.

        Raises:
            PermissionDeniedException: Invalid token or password requirements not met.
            NotFoundException: User not found.
        """
        try:
            payload = jwt_service.decode_token(data.token)
            jwt_service.verify_token_type(payload, "password_reset")

            user_id_str = payload.get("sub")
            email = payload.get("email")

            if not user_id_str or not email:
                raise PermissionDeniedException("Invalid reset token")

            user_id = UUID(user_id_str)

        except ValueError as e:
            raise PermissionDeniedException("Invalid or expired reset token") from e

        result = await db_session.execute(select(User).where(User.id == user_id, User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        if user.oauth_provider:
            raise PermissionDeniedException(f"This account uses {user.oauth_provider} login. Password cannot be reset.")

        is_valid, error_message = password_service.validate_password_strength(data.new_password)
        if not is_valid:
            raise PermissionDeniedException(error_message or "Password does not meet requirements")

        user.password_hash = password_service.hash_password(data.new_password)
        await db_session.commit()

        return VerifyEmailResponse(message="Password reset successfully")

    @post("/oauth/{provider:str}")
    async def oauth_login_post(
        self,
        provider: str,
        request: Request,
    ) -> Redirect:
        """Initiate OAuth login flow via POST (HTMX compatible).

        Same as GET /oauth/{provider} but accepts POST for HTMX buttons.
        """
        oauth_service = get_oauth_service(settings)

        try:
            oauth_provider = oauth_service.get_provider(provider)
        except ValueError as e:
            raise PermissionDeniedException(str(e)) from e

        state = secrets.token_urlsafe(32)
        request.set_session({"oauth_state": state, "oauth_provider": provider})

        redirect_uri = f"{settings.oauth_redirect_base_url}/api/auth/oauth/{provider}/callback"
        auth_url = oauth_provider.get_authorization_url(redirect_uri, state)

        return Redirect(path=auth_url)

    @put("/profile", guards=[require_authenticated])
    async def update_profile(
        self,
        data: ProfileUpdateRequest,
        current_user: User,
        db_session: AsyncSession,
    ) -> Response:
        """Update user profile information.

        Updates the authenticated user's profile fields including name,
        username, and email address.
        """
        if data.username != current_user.username:
            result = await db_session.execute(select(User).where(User.username == data.username))
            if result.scalar_one_or_none():
                raise PermissionDeniedException("Username already taken")

        if data.email != current_user.email:
            result = await db_session.execute(select(User).where(User.email == data.email))
            if result.scalar_one_or_none():
                raise PermissionDeniedException("Email already registered")
            current_user.email_verified = False

        current_user.first_name = data.first_name
        current_user.last_name = data.last_name
        current_user.username = data.username
        current_user.email = data.email

        await db_session.commit()

        return Response(
            content='<div class="alert alert-success">Profile updated successfully!</div>',
            media_type="text/html",
        )

    @post("/change-password", guards=[require_authenticated])
    async def change_password(
        self,
        data: ChangePasswordRequest,
        current_user: User,
        db_session: AsyncSession,
    ) -> Response:
        """Change password for authenticated user.

        Validates current password and updates to new password.
        """
        if current_user.oauth_provider:
            raise PermissionDeniedException(f"This account uses {current_user.oauth_provider} login")

        if not current_user.password_hash or not password_service.verify_password(
            data.current_password, current_user.password_hash
        ):
            return Response(
                content='<div class="alert alert-error">Current password is incorrect</div>',
                media_type="text/html",
            )

        if data.new_password != data.confirm_password:
            return Response(
                content='<div class="alert alert-error">New passwords do not match</div>',
                media_type="text/html",
            )

        is_valid, error_message = password_service.validate_password_strength(data.new_password)
        if not is_valid:
            return Response(
                content=f'<div class="alert alert-error">{error_message}</div>',
                media_type="text/html",
            )

        current_user.password_hash = password_service.hash_password(data.new_password)
        await db_session.commit()

        return Response(
            content='<div class="alert alert-success">Password changed successfully!</div>',
            media_type="text/html",
        )

    @put("/settings", guards=[require_authenticated])
    async def update_settings(
        self,
        data: SettingsUpdateRequest,
        current_user: User,
        db_session: AsyncSession,
    ) -> Response:
        """Update user account settings.

        Updates privacy and visibility preferences.
        """
        current_user.public_profile = data.public_profile

        try:
            current_user.email_privacy = EmailPrivacy(data.email_privacy)
        except ValueError:
            current_user.email_privacy = EmailPrivacy.PRIVATE

        try:
            current_user.search_visibility = SearchVisibility(data.search_visibility)
        except ValueError:
            current_user.search_visibility = SearchVisibility.PUBLIC

        await db_session.commit()

        return Response(
            content='<div class="alert alert-success">Settings saved successfully!</div>',
            media_type="text/html",
        )

    @delete("/account", guards=[require_authenticated], status_code=303)
    async def delete_account(
        self,
        current_user: User,
        db_session: AsyncSession,
    ) -> Redirect:
        """Delete user account permanently.

        Permanently deletes the authenticated user's account and all associated data.
        """
        await db_session.delete(current_user)
        await db_session.commit()

        return Redirect(path="/")


class AuthPageController(Controller):
    """Controller for authentication HTML pages."""

    path = "/auth"
    include_in_schema = False

    @get("/login")
    async def login_page(self) -> Template:
        """Render the login page."""
        return Template(
            template_name="auth/login.html.jinja2",
            context={
                "title": "Sign In",
                "description": "Sign in to your Python.org account",
            },
        )

    @get("/register")
    async def register_page(self) -> Template:
        """Render the registration page."""
        return Template(
            template_name="auth/register.html.jinja2",
            context={
                "title": "Create Account",
                "description": "Create a new Python.org account",
            },
        )

    @get("/profile", guards=[require_authenticated])
    async def profile_page(self, request: Request) -> Template:
        """Render the user profile page."""
        return Template(
            template_name="auth/profile.html.jinja2",
            context={
                "user": request.user,
                "title": "Your Profile",
                "description": "Manage your Python.org account",
            },
        )

    @get("/forgot-password")
    async def forgot_password_page(self) -> Template:
        """Render the forgot password page."""
        return Template(
            template_name="auth/forgot_password.html.jinja2",
            context={
                "title": "Reset Password",
                "description": "Reset your Python.org password",
            },
        )

    @get("/reset-password/{token:str}")
    async def reset_password_page(self, token: str) -> Template:
        """Render the password reset page."""
        return Template(
            template_name="auth/reset_password.html.jinja2",
            context={
                "token": token,
                "title": "Set New Password",
                "description": "Set a new password for your account",
            },
        )

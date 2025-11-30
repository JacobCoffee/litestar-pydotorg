"""Integration tests for OAuth2 routes."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from httpx import Response as HttpxResponse

from pydotorg.core.auth.oauth import OAuthUserInfo

if TYPE_CHECKING:
    from litestar.testing import AsyncTestClient


GITHUB_USER_DATA = {
    "id": 12345,
    "login": "testuser",
    "name": "Test User",
}

GITHUB_EMAILS_DATA = [
    {"email": "test@example.com", "primary": True, "verified": True},
    {"email": "secondary@example.com", "primary": False, "verified": True},
]

GOOGLE_USER_DATA = {
    "id": "google-123",
    "email": "test@gmail.com",
    "given_name": "Test",
    "family_name": "User",
    "verified_email": True,
}

TOKEN_RESPONSE = {
    "access_token": "mock-access-token",
    "token_type": "bearer",
    "scope": "user:email",
}


def create_mock_response(data: dict[str, Any], status_code: int = 200) -> Mock:
    """Create mock HTTP response for external API calls."""
    response = Mock()
    response.status_code = status_code
    response.json.return_value = data
    response.raise_for_status = Mock()
    return response


def create_mock_async_client(post_response: Mock | None = None, get_responses: list[Mock] | None = None) -> Mock:
    """Create a mock httpx.AsyncClient that works as async context manager."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    if post_response:
        mock_client.post = AsyncMock(return_value=post_response)

    if get_responses:
        mock_client.get = AsyncMock(side_effect=get_responses)
    elif post_response:
        mock_client.get = AsyncMock(return_value=create_mock_response({}))

    return mock_client


@pytest.mark.asyncio
class TestOAuthLoginInitiation:
    """Tests for OAuth login initiation endpoint."""

    async def test_github_oauth_redirects_to_github(self, client: AsyncTestClient) -> None:
        """Test GitHub OAuth redirects to GitHub authorization URL."""
        with patch("pydotorg.config.settings.github_client_id", "test-github-id"):
            response = await client.get("/api/auth/oauth/github", follow_redirects=False)

        assert response.status_code == 302
        location = response.headers["location"]
        assert "github.com/login/oauth/authorize" in location
        assert "client_id=test-github-id" in location
        assert "response_type=code" in location
        assert "scope=user%3Aemail" in location
        assert "state=" in location
        assert "redirect_uri=" in location

    async def test_google_oauth_redirects_to_google(self, client: AsyncTestClient) -> None:
        """Test Google OAuth redirects to Google authorization URL."""
        with patch("pydotorg.config.settings.google_client_id", "test-google-id"):
            response = await client.get("/api/auth/oauth/google", follow_redirects=False)

        assert response.status_code == 302
        location = response.headers["location"]
        assert "accounts.google.com/o/oauth2/v2/auth" in location
        assert "client_id=test-google-id" in location
        assert "response_type=code" in location
        assert "scope=openid+email+profile" in location
        assert "state=" in location
        assert "redirect_uri=" in location

    async def test_invalid_provider_returns_403(self, client: AsyncTestClient) -> None:
        """Test unknown provider returns 403 error."""
        response = await client.get("/api/auth/oauth/invalid_provider", follow_redirects=False)

        assert response.status_code == 403
        assert "Unknown OAuth provider" in response.text

    async def test_session_stores_state_and_provider(self, client: AsyncTestClient) -> None:
        """Test OAuth session stores state and provider for CSRF protection."""
        with patch("pydotorg.config.settings.github_client_id", "test-github-id"):
            response = await client.get("/api/auth/oauth/github", follow_redirects=False)

        assert response.status_code == 302

        location = response.headers["location"]
        state_param = [p.split("=")[1] for p in location.split("&") if p.startswith("state=")]
        assert len(state_param) == 1

    async def test_redirect_url_contains_correct_params(self, client: AsyncTestClient) -> None:
        """Test redirect URL contains all required OAuth parameters."""
        with patch("pydotorg.config.settings.github_client_id", "test-client-id"):
            response = await client.get("/api/auth/oauth/github", follow_redirects=False)

        location = response.headers["location"]
        assert "client_id=" in location
        assert "redirect_uri=" in location
        assert "response_type=code" in location
        assert "scope=" in location
        assert "state=" in location

    async def test_oauth_not_configured_returns_error(self, client: AsyncTestClient) -> None:
        """Test OAuth initiation fails when provider credentials not configured."""
        with patch("pydotorg.config.settings.github_client_id", None):
            response = await client.get("/api/auth/oauth/github", follow_redirects=False)

        assert response.status_code == 500

    async def test_github_redirect_uri_includes_callback_path(self, client: AsyncTestClient) -> None:
        """Test redirect URI includes correct callback path."""
        with (
            patch("pydotorg.config.settings.github_client_id", "test-id"),
            patch("pydotorg.config.settings.oauth_redirect_base_url", "http://localhost:8000"),
        ):
            response = await client.get("/api/auth/oauth/github", follow_redirects=False)

        location = response.headers["location"]
        assert "oauth%2Fgithub%2Fcallback" in location or "/api/auth/oauth/github/callback" in location

    async def test_state_is_url_safe(self, client: AsyncTestClient) -> None:
        """Test generated state token is URL-safe."""
        with patch("pydotorg.config.settings.github_client_id", "test-id"):
            response = await client.get("/api/auth/oauth/github", follow_redirects=False)

        location = response.headers["location"]
        state_value = next(
            (p.split("=")[1] for p in location.split("&") if p.startswith("state=")),
            None,
        )

        assert state_value is not None
        assert all(c.isalnum() or c in "-_%" for c in state_value)


@pytest.mark.asyncio
class TestOAuthCallbackSuccess:
    """Tests for successful OAuth callback flows."""

    async def test_successful_github_callback_creates_new_user(self, client: AsyncTestClient) -> None:
        """Test successful GitHub callback creates new user and returns JWT tokens."""
        mock_client = create_mock_async_client(
            post_response=create_mock_response(TOKEN_RESPONSE),
            get_responses=[
                create_mock_response(GITHUB_USER_DATA),
                create_mock_response(GITHUB_EMAILS_DATA),
            ],
        )

        with (
            patch("pydotorg.config.settings.github_client_id", "test-id"),
            patch("pydotorg.config.settings.github_client_secret", "test-secret"),
        ):
            init_response = await client.get("/api/auth/oauth/github", follow_redirects=False)
            assert init_response.status_code == 302

            location = init_response.headers["location"]
            state = next(
                (p.split("=")[1] for p in location.split("&") if p.startswith("state=")),
                None,
            )
            assert state is not None

            with patch("pydotorg.core.auth.oauth.httpx.AsyncClient", return_value=mock_client):
                callback_response = await client.get(
                    f"/api/auth/oauth/github/callback?code=test_code&state={state}",
                )

                assert callback_response.status_code == 200
                data = callback_response.json()
                assert "access_token" in data
                assert "refresh_token" in data
                assert data["token_type"] == "bearer"
                assert data["expires_in"] > 0

    async def test_successful_google_callback_creates_new_user(self, client: AsyncTestClient) -> None:
        """Test successful Google callback creates new user and returns JWT tokens."""
        mock_client = create_mock_async_client(
            post_response=create_mock_response(TOKEN_RESPONSE),
            get_responses=[create_mock_response(GOOGLE_USER_DATA)],
        )

        with (
            patch("pydotorg.config.settings.google_client_id", "test-id"),
            patch("pydotorg.config.settings.google_client_secret", "test-secret"),
        ):
            init_response = await client.get("/api/auth/oauth/google", follow_redirects=False)
            assert init_response.status_code == 302

            location = init_response.headers["location"]
            state = next(
                (p.split("=")[1] for p in location.split("&") if p.startswith("state=")),
                None,
            )

            with patch("pydotorg.core.auth.oauth.httpx.AsyncClient", return_value=mock_client):
                callback_response = await client.get(
                    f"/api/auth/oauth/google/callback?code=test_code&state={state}",
                )

                assert callback_response.status_code == 200
                data = callback_response.json()
                assert "access_token" in data
                assert "refresh_token" in data

    async def test_callback_returns_jwt_tokens(self, client: AsyncTestClient) -> None:
        """Test callback returns valid JWT access and refresh tokens."""
        mock_client = create_mock_async_client(
            post_response=create_mock_response(TOKEN_RESPONSE),
            get_responses=[
                create_mock_response(GITHUB_USER_DATA),
                create_mock_response(GITHUB_EMAILS_DATA),
            ],
        )

        with (
            patch("pydotorg.config.settings.github_client_id", "test-id"),
            patch("pydotorg.config.settings.github_client_secret", "test-secret"),
        ):
            init_response = await client.get("/api/auth/oauth/github", follow_redirects=False)
            location = init_response.headers["location"]
            state = next((p.split("=")[1] for p in location.split("&") if p.startswith("state=")), None)

            with patch("pydotorg.core.auth.oauth.httpx.AsyncClient", return_value=mock_client):
                callback_response = await client.get(
                    f"/api/auth/oauth/github/callback?code=test_code&state={state}",
                )

                assert callback_response.status_code == 200
                tokens = callback_response.json()

            me_response = await client.post(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )

            assert me_response.status_code == 200
            user_data = me_response.json()
            assert user_data["username"] == "testuser"
            assert user_data["email"] == "test@example.com"

    async def test_callback_with_existing_email_user_links_oauth(self, client: AsyncTestClient) -> None:
        """Test callback with existing email user links OAuth provider to account."""
        mock_client = create_mock_async_client(
            post_response=create_mock_response(TOKEN_RESPONSE),
            get_responses=[
                create_mock_response(GITHUB_USER_DATA),
                create_mock_response(GITHUB_EMAILS_DATA),
            ],
        )

        await client.post(
            "/api/auth/register",
            json={
                "username": "existinguser",
                "email": "test@example.com",
                "password": "SecurePass123!",
                "first_name": "Existing",
                "last_name": "User",
            },
        )

        with (
            patch("pydotorg.config.settings.github_client_id", "test-id"),
            patch("pydotorg.config.settings.github_client_secret", "test-secret"),
        ):
            init_response = await client.get("/api/auth/oauth/github", follow_redirects=False)
            location = init_response.headers["location"]
            state = next((p.split("=")[1] for p in location.split("&") if p.startswith("state=")), None)

            with patch("pydotorg.core.auth.oauth.httpx.AsyncClient", return_value=mock_client):
                callback_response = await client.get(
                    f"/api/auth/oauth/github/callback?code=test_code&state={state}",
                )

                assert callback_response.status_code == 200
                tokens = callback_response.json()

            me_response = await client.post(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            user_data = me_response.json()
            assert user_data["email"] == "test@example.com"
            assert user_data["username"] == "existinguser"

    async def test_username_collision_appends_random_suffix(self, client: AsyncTestClient) -> None:
        """Test username collision during OAuth registration appends random suffix."""
        mock_client = create_mock_async_client(
            post_response=create_mock_response(TOKEN_RESPONSE),
            get_responses=[
                create_mock_response(GITHUB_USER_DATA),
                create_mock_response(GITHUB_EMAILS_DATA),
            ],
        )

        await client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "existing@example.com",
                "password": "SecurePass123!",
                "first_name": "Existing",
                "last_name": "User",
            },
        )

        with (
            patch("pydotorg.config.settings.github_client_id", "test-id"),
            patch("pydotorg.config.settings.github_client_secret", "test-secret"),
        ):
            init_response = await client.get("/api/auth/oauth/github", follow_redirects=False)
            location = init_response.headers["location"]
            state = next((p.split("=")[1] for p in location.split("&") if p.startswith("state=")), None)

            with patch("pydotorg.core.auth.oauth.httpx.AsyncClient", return_value=mock_client):
                callback_response = await client.get(
                    f"/api/auth/oauth/github/callback?code=test_code&state={state}",
                )

                assert callback_response.status_code == 200
                tokens = callback_response.json()

            me_response = await client.post(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            user_data = me_response.json()
            assert user_data["username"].startswith("testuser_")
            assert len(user_data["username"]) > len("testuser_")


@pytest.mark.asyncio
class TestOAuthCallbackErrors:
    """Tests for OAuth callback error handling."""

    async def test_callback_with_invalid_state_returns_403(self, client: AsyncTestClient) -> None:
        """Test callback with invalid state parameter returns 403."""
        with patch("pydotorg.config.settings.github_client_id", "test-id"):
            await client.get("/api/auth/oauth/github", follow_redirects=False)

            callback_response = await client.get(
                "/api/auth/oauth/github/callback?code=test_code&state=invalid_state",
            )

            assert callback_response.status_code == 403
            assert "Invalid OAuth state" in callback_response.text

    async def test_callback_with_missing_state_returns_error(self, client: AsyncTestClient) -> None:
        """Test callback with missing state parameter returns error."""
        with patch("pydotorg.config.settings.github_client_id", "test-id"):
            await client.get("/api/auth/oauth/github", follow_redirects=False)

            callback_response = await client.get(
                "/api/auth/oauth/github/callback?code=test_code",
            )

            assert callback_response.status_code in (400, 422, 403)

    async def test_callback_with_provider_mismatch_returns_403(self, client: AsyncTestClient) -> None:
        """Test callback with mismatched provider returns 403."""
        with patch("pydotorg.config.settings.github_client_id", "test-id"):
            init_response = await client.get("/api/auth/oauth/github", follow_redirects=False)
            location = init_response.headers["location"]
            github_state = next((p.split("=")[1] for p in location.split("&") if p.startswith("state=")), None)

            callback_response = await client.get(
                f"/api/auth/oauth/google/callback?code=test_code&state={github_state}",
            )

            assert callback_response.status_code == 403
            assert "OAuth provider mismatch" in callback_response.text

    async def test_callback_with_no_access_token_in_response_returns_403(self, client: AsyncTestClient) -> None:
        """Test callback when token exchange returns no access token."""
        mock_client = create_mock_async_client(
            post_response=create_mock_response({"token_type": "bearer"}),
        )

        with (
            patch("pydotorg.config.settings.github_client_id", "test-id"),
            patch("pydotorg.config.settings.github_client_secret", "test-secret"),
        ):
            init_response = await client.get("/api/auth/oauth/github", follow_redirects=False)
            location = init_response.headers["location"]
            state = next((p.split("=")[1] for p in location.split("&") if p.startswith("state=")), None)

            with patch("pydotorg.core.auth.oauth.httpx.AsyncClient", return_value=mock_client):
                callback_response = await client.get(
                    f"/api/auth/oauth/github/callback?code=test_code&state={state}",
                )

            assert callback_response.status_code == 403
            assert "Failed to obtain access token" in callback_response.text

    async def test_callback_email_already_registered_with_different_oauth_returns_403(
        self,
        client: AsyncTestClient,
    ) -> None:
        """Test callback when email already registered with different OAuth provider."""
        github_mock = create_mock_async_client(
            post_response=create_mock_response(TOKEN_RESPONSE),
            get_responses=[
                create_mock_response(GITHUB_USER_DATA),
                create_mock_response(GITHUB_EMAILS_DATA),
            ],
        )

        with (
            patch("pydotorg.config.settings.github_client_id", "test-id"),
            patch("pydotorg.config.settings.github_client_secret", "test-secret"),
        ):
            init_response = await client.get("/api/auth/oauth/github", follow_redirects=False)
            location = init_response.headers["location"]
            state = next((p.split("=")[1] for p in location.split("&") if p.startswith("state=")), None)

            with patch("pydotorg.core.auth.oauth.httpx.AsyncClient", return_value=github_mock):
                await client.get(
                    f"/api/auth/oauth/github/callback?code=test_code&state={state}",
                )

        google_data = GOOGLE_USER_DATA.copy()
        google_data["email"] = "test@example.com"

        google_mock = create_mock_async_client(
            post_response=create_mock_response(TOKEN_RESPONSE),
            get_responses=[create_mock_response(google_data)],
        )

        with (
            patch("pydotorg.config.settings.google_client_id", "test-id"),
            patch("pydotorg.config.settings.google_client_secret", "test-secret"),
        ):
            init_response = await client.get("/api/auth/oauth/google", follow_redirects=False)
            location = init_response.headers["location"]
            state = next((p.split("=")[1] for p in location.split("&") if p.startswith("state=")), None)

            with patch("pydotorg.core.auth.oauth.httpx.AsyncClient", return_value=google_mock):
                callback_response = await client.get(
                    f"/api/auth/oauth/google/callback?code=test_code2&state={state}",
                )

                assert callback_response.status_code == 403
                assert "already registered with" in callback_response.text

    async def test_callback_with_unknown_provider_returns_403(self, client: AsyncTestClient) -> None:
        """Test callback with unknown provider returns 403."""
        callback_response = await client.get(
            "/api/auth/oauth/unknown/callback?code=test_code&state=some_state",
        )

        assert callback_response.status_code in (403, 500)

    async def test_callback_missing_code_parameter_returns_error(self, client: AsyncTestClient) -> None:
        """Test callback without code parameter returns error."""
        with patch("pydotorg.config.settings.github_client_id", "test-id"):
            init_response = await client.get("/api/auth/oauth/github", follow_redirects=False)
            location = init_response.headers["location"]
            state = next((p.split("=")[1] for p in location.split("&") if p.startswith("state=")), None)

            callback_response = await client.get(
                f"/api/auth/oauth/github/callback?state={state}",
            )

            assert callback_response.status_code in (400, 422, 403)


@pytest.mark.asyncio
class TestSessionStateManagement:
    """Tests for OAuth session state management and CSRF protection."""

    async def test_session_state_prevents_csrf(self, client: AsyncTestClient) -> None:
        """Test session state prevents CSRF attacks."""
        with patch("pydotorg.config.settings.github_client_id", "test-id"):
            init_response = await client.get("/api/auth/oauth/github", follow_redirects=False)

        assert init_response.status_code == 302

        different_state = secrets.token_urlsafe(32)
        callback_response = await client.get(
            f"/api/auth/oauth/github/callback?code=test_code&state={different_state}",
        )

        assert callback_response.status_code == 403
        assert "Invalid OAuth state" in callback_response.text

    async def test_multiple_concurrent_oauth_flows_dont_interfere(self, client: AsyncTestClient) -> None:
        """Test multiple concurrent OAuth flows don't interfere with each other."""
        with (
            patch("pydotorg.config.settings.github_client_id", "test-id"),
            patch("pydotorg.config.settings.google_client_id", "test-google-id"),
        ):
            github_response = await client.get("/api/auth/oauth/github", follow_redirects=False)
            google_response = await client.get("/api/auth/oauth/google", follow_redirects=False)

            assert github_response.status_code == 302
            assert google_response.status_code == 302

            github_location = github_response.headers["location"]
            google_location = google_response.headers["location"]

            assert "github.com" in github_location
            assert "google.com" in google_location

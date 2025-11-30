"""Unit tests for OAuth2 providers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest

from pydotorg.core.auth.oauth import (
    GitHubOAuthProvider,
    GoogleOAuthProvider,
    OAuthService,
    OAuthUserInfo,
    get_oauth_service,
)

if TYPE_CHECKING:
    pass


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create mock settings with OAuth credentials."""
    settings = MagicMock()
    settings.github_client_id = "test-github-client-id"
    settings.github_client_secret = "test-github-client-secret"
    settings.google_client_id = "test-google-client-id"
    settings.google_client_secret = "test-google-client-secret"
    settings.oauth_redirect_base_url = "http://localhost:8000"
    return settings


@pytest.fixture
def mock_settings_no_oauth() -> MagicMock:
    """Create mock settings without OAuth credentials."""
    settings = MagicMock()
    settings.github_client_id = None
    settings.github_client_secret = None
    settings.google_client_id = None
    settings.google_client_secret = None
    settings.oauth_redirect_base_url = "http://localhost:8000"
    return settings


@pytest.fixture
def mock_settings_github_only() -> MagicMock:
    """Create mock settings with only GitHub OAuth configured."""
    settings = MagicMock()
    settings.github_client_id = "test-github-client-id"
    settings.github_client_secret = "test-github-client-secret"
    settings.google_client_id = None
    settings.google_client_secret = None
    settings.oauth_redirect_base_url = "http://localhost:8000"
    return settings


class TestOAuthUserInfo:
    """Tests for OAuthUserInfo dataclass."""

    def test_create_oauth_user_info_all_fields(self) -> None:
        """Test creating OAuthUserInfo with all fields."""
        user_info = OAuthUserInfo(
            provider="github",
            oauth_id="123456",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            username="johndoe",
            email_verified=True,
        )

        assert user_info.provider == "github"
        assert user_info.oauth_id == "123456"
        assert user_info.email == "test@example.com"
        assert user_info.first_name == "John"
        assert user_info.last_name == "Doe"
        assert user_info.username == "johndoe"
        assert user_info.email_verified is True

    def test_create_oauth_user_info_with_empty_names(self) -> None:
        """Test creating OAuthUserInfo with empty optional fields."""
        user_info = OAuthUserInfo(
            provider="google",
            oauth_id="987654",
            email="user@gmail.com",
            first_name="",
            last_name="",
            username="user",
            email_verified=False,
        )

        assert user_info.provider == "google"
        assert user_info.oauth_id == "987654"
        assert user_info.email == "user@gmail.com"
        assert user_info.first_name == ""
        assert user_info.last_name == ""
        assert user_info.username == "user"
        assert user_info.email_verified is False

    def test_oauth_user_info_field_access(self) -> None:
        """Test field access on OAuthUserInfo."""
        user_info = OAuthUserInfo(
            provider="github",
            oauth_id="11111",
            email="access@test.com",
            first_name="Access",
            last_name="Test",
            username="accesstest",
            email_verified=True,
        )

        assert hasattr(user_info, "provider")
        assert hasattr(user_info, "oauth_id")
        assert hasattr(user_info, "email")
        assert hasattr(user_info, "first_name")
        assert hasattr(user_info, "last_name")
        assert hasattr(user_info, "username")
        assert hasattr(user_info, "email_verified")


class TestOAuthProviderBase:
    """Tests for OAuthProvider base class."""

    def test_get_authorization_url_generates_correct_url(self, mock_settings: MagicMock) -> None:
        """Test get_authorization_url generates URL with all required params."""
        provider = GitHubOAuthProvider(mock_settings)
        redirect_uri = "http://localhost:8000/auth/callback/github"
        state = "random-state-string"

        url = provider.get_authorization_url(redirect_uri, state)

        assert "https://github.com/login/oauth/authorize?" in url
        assert "client_id=test-github-client-id" in url
        assert "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fauth%2Fcallback%2Fgithub" in url
        assert "response_type=code" in url
        assert "scope=user%3Aemail" in url
        assert f"state={state}" in url

    def test_get_authorization_url_raises_when_client_id_none(self, mock_settings_no_oauth: MagicMock) -> None:
        """Test get_authorization_url raises ValueError when client_id is None."""
        provider = GitHubOAuthProvider(mock_settings_no_oauth)
        redirect_uri = "http://localhost:8000/auth/callback/github"
        state = "random-state"

        with pytest.raises(ValueError, match="github OAuth is not configured"):
            provider.get_authorization_url(redirect_uri, state)

    def test_url_contains_all_required_params(self, mock_settings: MagicMock) -> None:
        """Test generated URL contains all required OAuth parameters."""
        provider = GoogleOAuthProvider(mock_settings)
        redirect_uri = "http://localhost:8000/auth/callback/google"
        state = "test-state-123"

        url = provider.get_authorization_url(redirect_uri, state)

        assert "client_id=" in url
        assert "redirect_uri=" in url
        assert "response_type=code" in url
        assert "scope=" in url
        assert "state=" in url

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_raises_when_not_configured(self, mock_settings_no_oauth: MagicMock) -> None:
        """Test exchange_code_for_token raises when credentials not configured."""
        provider = GitHubOAuthProvider(mock_settings_no_oauth)
        code = "test-auth-code"
        redirect_uri = "http://localhost:8000/auth/callback/github"

        with pytest.raises(ValueError, match="github OAuth is not configured"):
            await provider.exchange_code_for_token(code, redirect_uri)

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_raises_when_client_secret_none(
        self, mock_settings_github_only: MagicMock
    ) -> None:
        """Test exchange_code_for_token raises when client_secret is None but client_id exists."""
        mock_settings_github_only.github_client_secret = None
        provider = GitHubOAuthProvider(mock_settings_github_only)
        code = "test-auth-code"
        redirect_uri = "http://localhost:8000/auth/callback/github"

        with pytest.raises(ValueError, match="github OAuth is not configured"):
            await provider.exchange_code_for_token(code, redirect_uri)


class TestGitHubOAuthProvider:
    """Tests for GitHubOAuthProvider."""

    def test_provider_name_returns_github(self, mock_settings: MagicMock) -> None:
        """Test provider_name property returns 'github'."""
        provider = GitHubOAuthProvider(mock_settings)
        assert provider.provider_name == "github"

    def test_authorize_url_is_correct(self, mock_settings: MagicMock) -> None:
        """Test authorize_url returns correct GitHub OAuth URL."""
        provider = GitHubOAuthProvider(mock_settings)
        assert provider.authorize_url == "https://github.com/login/oauth/authorize"

    def test_token_url_is_correct(self, mock_settings: MagicMock) -> None:
        """Test token_url returns correct GitHub token exchange URL."""
        provider = GitHubOAuthProvider(mock_settings)
        assert provider.token_url == "https://github.com/login/oauth/access_token"

    def test_user_info_url_is_correct(self, mock_settings: MagicMock) -> None:
        """Test user_info_url returns correct GitHub API URL."""
        provider = GitHubOAuthProvider(mock_settings)
        assert provider.user_info_url == "https://api.github.com/user"

    def test_scope_returns_user_email(self, mock_settings: MagicMock) -> None:
        """Test scope property returns 'user:email'."""
        provider = GitHubOAuthProvider(mock_settings)
        assert provider.scope == "user:email"

    def test_client_id_returns_settings_value(self, mock_settings: MagicMock) -> None:
        """Test client_id returns value from settings."""
        provider = GitHubOAuthProvider(mock_settings)
        assert provider.client_id == "test-github-client-id"

    def test_client_secret_returns_settings_value(self, mock_settings: MagicMock) -> None:
        """Test client_secret returns value from settings."""
        provider = GitHubOAuthProvider(mock_settings)
        assert provider.client_secret == "test-github-client-secret"

    def test_get_authorization_url_generates_valid_github_url(self, mock_settings: MagicMock) -> None:
        """Test get_authorization_url generates valid GitHub authorization URL."""
        provider = GitHubOAuthProvider(mock_settings)
        redirect_uri = "http://localhost:8000/auth/callback/github"
        state = "github-state-token"

        url = provider.get_authorization_url(redirect_uri, state)

        assert url.startswith("https://github.com/login/oauth/authorize?")
        assert "client_id=test-github-client-id" in url
        assert "scope=user%3Aemail" in url
        assert f"state={state}" in url

    @pytest.mark.asyncio
    async def test_get_user_info_parses_github_response(self, mock_settings: MagicMock) -> None:
        """Test get_user_info parses GitHub user response correctly."""
        provider = GitHubOAuthProvider(mock_settings)

        mock_user_response = Mock()
        mock_user_response.json.return_value = {
            "id": 123456,
            "login": "testuser",
            "name": "Test User",
        }
        mock_user_response.raise_for_status = Mock()

        mock_email_response = Mock()
        mock_email_response.json.return_value = [{"email": "test@example.com", "primary": True, "verified": True}]
        mock_email_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(side_effect=[mock_user_response, mock_email_response])
            mock_client_class.return_value = mock_client

            user_info = await provider.get_user_info("test-access-token")

        assert user_info.provider == "github"
        assert user_info.oauth_id == "123456"
        assert user_info.email == "test@example.com"
        assert user_info.first_name == "Test"
        assert user_info.last_name == "User"
        assert user_info.username == "testuser"
        assert user_info.email_verified is True

    @pytest.mark.asyncio
    async def test_get_user_info_extracts_primary_email(self, mock_settings: MagicMock) -> None:
        """Test get_user_info extracts primary email from emails list."""
        provider = GitHubOAuthProvider(mock_settings)

        mock_user_response = Mock()
        mock_user_response.json.return_value = {
            "id": 789012,
            "login": "emailtest",
            "name": "Email Test",
        }
        mock_user_response.raise_for_status = Mock()

        mock_email_response = Mock()
        mock_email_response.json.return_value = [
            {"email": "secondary@example.com", "primary": False, "verified": True},
            {"email": "primary@example.com", "primary": True, "verified": True},
            {"email": "other@example.com", "primary": False, "verified": False},
        ]
        mock_email_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(side_effect=[mock_user_response, mock_email_response])
            mock_client_class.return_value = mock_client

            user_info = await provider.get_user_info("test-token")

        assert user_info.email == "primary@example.com"
        assert user_info.email_verified is True

    @pytest.mark.asyncio
    async def test_get_user_info_handles_missing_name(self, mock_settings: MagicMock) -> None:
        """Test get_user_info handles missing name field gracefully."""
        provider = GitHubOAuthProvider(mock_settings)

        mock_user_response = Mock()
        mock_user_response.json.return_value = {
            "id": 111222,
            "login": "noname",
        }
        mock_user_response.raise_for_status = Mock()

        mock_email_response = Mock()
        mock_email_response.json.return_value = [{"email": "noname@example.com", "primary": True, "verified": False}]
        mock_email_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(side_effect=[mock_user_response, mock_email_response])
            mock_client_class.return_value = mock_client

            user_info = await provider.get_user_info("test-token")

        assert user_info.first_name == ""
        assert user_info.last_name == ""
        assert user_info.username == "noname"

    @pytest.mark.asyncio
    async def test_get_user_info_raises_when_no_email(self, mock_settings: MagicMock) -> None:
        """Test get_user_info raises ValueError when no email found."""
        provider = GitHubOAuthProvider(mock_settings)

        mock_user_response = Mock()
        mock_user_response.json.return_value = {
            "id": 333444,
            "login": "noemail",
            "name": "No Email",
        }
        mock_user_response.raise_for_status = Mock()

        mock_email_response = Mock()
        mock_email_response.json.return_value = []
        mock_email_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(side_effect=[mock_user_response, mock_email_response])
            mock_client_class.return_value = mock_client

            with pytest.raises(ValueError, match="No email found in GitHub account"):
                await provider.get_user_info("test-token")

    @pytest.mark.asyncio
    async def test_get_user_info_handles_single_name(self, mock_settings: MagicMock) -> None:
        """Test get_user_info correctly splits single-word names."""
        provider = GitHubOAuthProvider(mock_settings)

        mock_user_response = Mock()
        mock_user_response.json.return_value = {
            "id": 555666,
            "login": "singlename",
            "name": "Madonna",
        }
        mock_user_response.raise_for_status = Mock()

        mock_email_response = Mock()
        mock_email_response.json.return_value = [{"email": "madonna@example.com", "primary": True, "verified": True}]
        mock_email_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(side_effect=[mock_user_response, mock_email_response])
            mock_client_class.return_value = mock_client

            user_info = await provider.get_user_info("test-token")

        assert user_info.first_name == "Madonna"
        assert user_info.last_name == ""


class TestGoogleOAuthProvider:
    """Tests for GoogleOAuthProvider."""

    def test_provider_name_returns_google(self, mock_settings: MagicMock) -> None:
        """Test provider_name property returns 'google'."""
        provider = GoogleOAuthProvider(mock_settings)
        assert provider.provider_name == "google"

    def test_authorize_url_is_correct(self, mock_settings: MagicMock) -> None:
        """Test authorize_url returns correct Google OAuth URL."""
        provider = GoogleOAuthProvider(mock_settings)
        assert provider.authorize_url == "https://accounts.google.com/o/oauth2/v2/auth"

    def test_token_url_is_correct(self, mock_settings: MagicMock) -> None:
        """Test token_url returns correct Google token exchange URL."""
        provider = GoogleOAuthProvider(mock_settings)
        assert provider.token_url == "https://oauth2.googleapis.com/token"

    def test_user_info_url_is_correct(self, mock_settings: MagicMock) -> None:
        """Test user_info_url returns correct Google API URL."""
        provider = GoogleOAuthProvider(mock_settings)
        assert provider.user_info_url == "https://www.googleapis.com/oauth2/v2/userinfo"

    def test_scope_returns_openid_email_profile(self, mock_settings: MagicMock) -> None:
        """Test scope property returns 'openid email profile'."""
        provider = GoogleOAuthProvider(mock_settings)
        assert provider.scope == "openid email profile"

    def test_client_id_returns_settings_value(self, mock_settings: MagicMock) -> None:
        """Test client_id returns value from settings."""
        provider = GoogleOAuthProvider(mock_settings)
        assert provider.client_id == "test-google-client-id"

    def test_client_secret_returns_settings_value(self, mock_settings: MagicMock) -> None:
        """Test client_secret returns value from settings."""
        provider = GoogleOAuthProvider(mock_settings)
        assert provider.client_secret == "test-google-client-secret"

    def test_get_authorization_url_generates_valid_google_url(self, mock_settings: MagicMock) -> None:
        """Test get_authorization_url generates valid Google authorization URL."""
        provider = GoogleOAuthProvider(mock_settings)
        redirect_uri = "http://localhost:8000/auth/callback/google"
        state = "google-state-token"

        url = provider.get_authorization_url(redirect_uri, state)

        assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
        assert "client_id=test-google-client-id" in url
        assert "scope=openid+email+profile" in url
        assert f"state={state}" in url

    @pytest.mark.asyncio
    async def test_get_user_info_parses_google_response(self, mock_settings: MagicMock) -> None:
        """Test get_user_info parses Google user response correctly."""
        provider = GoogleOAuthProvider(mock_settings)

        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "google-user-id-123",
            "email": "googleuser@gmail.com",
            "given_name": "Google",
            "family_name": "User",
            "verified_email": True,
        }
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            user_info = await provider.get_user_info("test-google-token")

        assert user_info.provider == "google"
        assert user_info.oauth_id == "google-user-id-123"
        assert user_info.email == "googleuser@gmail.com"
        assert user_info.first_name == "Google"
        assert user_info.last_name == "User"
        assert user_info.username == "googleuser"
        assert user_info.email_verified is True

    @pytest.mark.asyncio
    async def test_get_user_info_generates_username_from_email(self, mock_settings: MagicMock) -> None:
        """Test get_user_info generates username from email local part."""
        provider = GoogleOAuthProvider(mock_settings)

        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "456789",
            "email": "jane.doe@example.com",
            "given_name": "Jane",
            "family_name": "Doe",
            "verified_email": True,
        }
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            user_info = await provider.get_user_info("test-token")

        assert user_info.username == "jane.doe"
        assert user_info.email == "jane.doe@example.com"

    @pytest.mark.asyncio
    async def test_get_user_info_handles_missing_names(self, mock_settings: MagicMock) -> None:
        """Test get_user_info handles missing given_name and family_name."""
        provider = GoogleOAuthProvider(mock_settings)

        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "999888",
            "email": "minimal@gmail.com",
            "verified_email": False,
        }
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            user_info = await provider.get_user_info("test-token")

        assert user_info.first_name == ""
        assert user_info.last_name == ""
        assert user_info.username == "minimal"
        assert user_info.email_verified is False


class TestOAuthService:
    """Tests for OAuthService."""

    def test_service_initializes_with_both_providers(self, mock_settings: MagicMock) -> None:
        """Test OAuthService initializes with GitHub and Google providers."""
        service = OAuthService(mock_settings)

        assert "github" in service.providers
        assert "google" in service.providers
        assert isinstance(service.providers["github"], GitHubOAuthProvider)
        assert isinstance(service.providers["google"], GoogleOAuthProvider)

    def test_get_provider_github_returns_github_provider(self, mock_settings: MagicMock) -> None:
        """Test get_provider('github') returns GitHubOAuthProvider."""
        service = OAuthService(mock_settings)

        provider = service.get_provider("github")

        assert isinstance(provider, GitHubOAuthProvider)
        assert provider.provider_name == "github"

    def test_get_provider_google_returns_google_provider(self, mock_settings: MagicMock) -> None:
        """Test get_provider('google') returns GoogleOAuthProvider."""
        service = OAuthService(mock_settings)

        provider = service.get_provider("google")

        assert isinstance(provider, GoogleOAuthProvider)
        assert provider.provider_name == "google"

    def test_get_provider_unknown_raises_value_error(self, mock_settings: MagicMock) -> None:
        """Test get_provider raises ValueError for unknown provider."""
        service = OAuthService(mock_settings)

        with pytest.raises(ValueError, match="Unknown OAuth provider: facebook"):
            service.get_provider("facebook")

    def test_get_oauth_service_factory_function(self, mock_settings: MagicMock) -> None:
        """Test get_oauth_service factory function returns OAuthService."""
        service = get_oauth_service(mock_settings)

        assert isinstance(service, OAuthService)
        assert "github" in service.providers
        assert "google" in service.providers

    def test_service_providers_use_same_settings(self, mock_settings: MagicMock) -> None:
        """Test all providers in service use the same settings instance."""
        service = OAuthService(mock_settings)

        github_provider = service.get_provider("github")
        google_provider = service.get_provider("google")

        assert github_provider.settings is mock_settings
        assert google_provider.settings is mock_settings


class TestTokenExchange:
    """Tests for token exchange functionality."""

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_makes_correct_post_request(self, mock_settings: MagicMock) -> None:
        """Test exchange_code_for_token makes correct POST request to token endpoint."""
        provider = GitHubOAuthProvider(mock_settings)
        code = "auth-code-123"
        redirect_uri = "http://localhost:8000/auth/callback/github"

        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "github-access-token",
            "token_type": "bearer",
            "scope": "user:email",
        }
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await provider.exchange_code_for_token(code, redirect_uri)

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "https://github.com/login/oauth/access_token"
            assert call_args[1]["data"]["client_id"] == "test-github-client-id"
            assert call_args[1]["data"]["client_secret"] == "test-github-client-secret"
            assert call_args[1]["data"]["code"] == code
            assert call_args[1]["data"]["redirect_uri"] == redirect_uri
            assert call_args[1]["data"]["grant_type"] == "authorization_code"
            assert call_args[1]["headers"]["Accept"] == "application/json"

        assert result["access_token"] == "github-access-token"
        assert result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_returns_parsed_json(self, mock_settings: MagicMock) -> None:
        """Test exchange_code_for_token returns parsed JSON response."""
        provider = GoogleOAuthProvider(mock_settings)
        code = "google-auth-code"
        redirect_uri = "http://localhost:8000/auth/callback/google"

        expected_response = {
            "access_token": "google-access-token-xyz",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "openid email profile",
            "id_token": "eyJ...",
        }

        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await provider.exchange_code_for_token(code, redirect_uri)

        assert result == expected_response
        assert result["access_token"] == "google-access-token-xyz"
        assert result["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_handles_http_errors(self, mock_settings: MagicMock) -> None:
        """Test exchange_code_for_token propagates HTTP errors."""
        provider = GitHubOAuthProvider(mock_settings)
        code = "invalid-code"
        redirect_uri = "http://localhost:8000/auth/callback/github"

        mock_response = Mock()
        mock_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError("Bad Request", request=Mock(), response=Mock())
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await provider.exchange_code_for_token(code, redirect_uri)

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_requires_both_credentials(
        self, mock_settings_github_only: MagicMock
    ) -> None:
        """Test exchange_code_for_token requires both client_id and client_secret."""
        mock_settings_github_only.github_client_secret = None
        provider = GitHubOAuthProvider(mock_settings_github_only)
        code = "test-code"
        redirect_uri = "http://localhost:8000/auth/callback/github"

        with pytest.raises(ValueError, match="github OAuth is not configured"):
            await provider.exchange_code_for_token(code, redirect_uri)

        mock_settings_github_only.github_client_id = None
        mock_settings_github_only.github_client_secret = "test-secret"
        provider = GitHubOAuthProvider(mock_settings_github_only)

        with pytest.raises(ValueError, match="github OAuth is not configured"):
            await provider.exchange_code_for_token(code, redirect_uri)

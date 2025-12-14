"""OAuth2 authentication providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

import httpx

if TYPE_CHECKING:
    from pydotorg.config import Settings


@dataclass
class OAuthUserInfo:
    provider: str
    oauth_id: str
    email: str
    first_name: str
    last_name: str
    username: str
    email_verified: bool


class OAuthProvider(ABC):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def authorize_url(self) -> str:
        pass

    @property
    @abstractmethod
    def token_url(self) -> str:
        pass

    @property
    @abstractmethod
    def user_info_url(self) -> str:
        pass

    @property
    @abstractmethod
    def client_id(self) -> str | None:
        pass

    @property
    @abstractmethod
    def client_secret(self) -> str | None:
        pass

    @property
    @abstractmethod
    def scope(self) -> str:
        pass

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        if not self.client_id:
            msg = f"{self.provider_name} OAuth is not configured"
            raise ValueError(msg)

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "state": state,
        }
        return f"{self.authorize_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict[str, Any]:
        if not self.client_id or not self.client_secret:
            msg = f"{self.provider_name} OAuth is not configured"
            raise ValueError(msg)

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data=data,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    @abstractmethod
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        pass


class GitHubOAuthProvider(OAuthProvider):
    @property
    def provider_name(self) -> str:
        return "github"

    @property
    def authorize_url(self) -> str:
        return "https://github.com/login/oauth/authorize"

    @property
    def token_url(self) -> str:
        return "https://github.com/login/oauth/access_token"

    @property
    def user_info_url(self) -> str:
        return "https://api.github.com/user"

    @property
    def client_id(self) -> str | None:
        return self.settings.github_client_id

    @property
    def client_secret(self) -> str | None:
        return self.settings.github_client_secret

    @property
    def scope(self) -> str:
        return "user:email"

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                self.user_info_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_response.raise_for_status()
            user_data = user_response.json()

            email_response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            email_response.raise_for_status()
            emails = email_response.json()

            primary_email = next((e for e in emails if e["primary"]), emails[0] if emails else None)

            if not primary_email:
                msg = "No email found in GitHub account"
                raise ValueError(msg)

            name_parts = (user_data.get("name") or "").split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            return OAuthUserInfo(
                provider=self.provider_name,
                oauth_id=str(user_data["id"]),
                email=primary_email["email"],
                first_name=first_name,
                last_name=last_name,
                username=user_data["login"],
                email_verified=primary_email.get("verified", False),
            )


class GoogleOAuthProvider(OAuthProvider):
    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def authorize_url(self) -> str:
        return "https://accounts.google.com/o/oauth2/v2/auth"

    @property
    def token_url(self) -> str:
        return "https://oauth2.googleapis.com/token"

    @property
    def user_info_url(self) -> str:
        return "https://www.googleapis.com/oauth2/v2/userinfo"

    @property
    def client_id(self) -> str | None:
        return self.settings.google_client_id

    @property
    def client_secret(self) -> str | None:
        return self.settings.google_client_secret

    @property
    def scope(self) -> str:
        return "openid email profile"

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.user_info_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            user_data = response.json()

            username = user_data.get("email", "").split("@")[0]

            return OAuthUserInfo(
                provider=self.provider_name,
                oauth_id=user_data["id"],
                email=user_data["email"],
                first_name=user_data.get("given_name", ""),
                last_name=user_data.get("family_name", ""),
                username=username,
                email_verified=user_data.get("verified_email", False),
            )


class DiscordOAuthProvider(OAuthProvider):
    @property
    def provider_name(self) -> str:
        return "discord"

    @property
    def authorize_url(self) -> str:
        return "https://discord.com/api/oauth2/authorize"

    @property
    def token_url(self) -> str:
        return "https://discord.com/api/oauth2/token"

    @property
    def user_info_url(self) -> str:
        return "https://discord.com/api/users/@me"

    @property
    def client_id(self) -> str | None:
        return self.settings.discord_client_id

    @property
    def client_secret(self) -> str | None:
        return self.settings.discord_client_secret

    @property
    def scope(self) -> str:
        return "identify email"

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.user_info_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            user_data = response.json()

            email = user_data.get("email")
            if not email:
                msg = "No email found in Discord account. Please enable email access."
                raise ValueError(msg)

            global_name = user_data.get("global_name") or user_data.get("username", "")
            name_parts = global_name.split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            return OAuthUserInfo(
                provider=self.provider_name,
                oauth_id=user_data["id"],
                email=email,
                first_name=first_name,
                last_name=last_name,
                username=user_data.get("username", email.split("@")[0]),
                email_verified=user_data.get("verified", False),
            )


class OAuthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.providers: dict[str, OAuthProvider] = {
            "github": GitHubOAuthProvider(settings),
            "google": GoogleOAuthProvider(settings),
            "discord": DiscordOAuthProvider(settings),
        }

    def get_provider(self, provider_name: str) -> OAuthProvider:
        provider = self.providers.get(provider_name)
        if not provider:
            msg = f"Unknown OAuth provider: {provider_name}"
            raise ValueError(msg)
        return provider


def get_oauth_service(settings: Settings) -> OAuthService:
    return OAuthService(settings)

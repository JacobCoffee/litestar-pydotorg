"""Authentication endpoints integration tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from pydotorg.core.auth.password import password_service
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from litestar.testing import AsyncTestClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=password_service.hash_password("TestPassword123"),
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.skip(reason="Integration tests need database isolation refactoring")
@pytest.mark.asyncio
class TestAuthEndpoints:
    async def test_register_success(self, client: AsyncTestClient, db_session: AsyncSession) -> None:
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePass123",
                "first_name": "New",
                "last_name": "User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

        result = await db_session.execute(select(User).where(User.username == "newuser"))
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.first_name == "New"

    async def test_register_duplicate_username(self, client: AsyncTestClient, test_user: User) -> None:
        response = await client.post(
            "/api/auth/register",
            json={
                "username": test_user.username,
                "email": "different@example.com",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 403
        assert "Username already exists" in response.text

    async def test_register_duplicate_email(self, client: AsyncTestClient, test_user: User) -> None:
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "differentuser",
                "email": test_user.email,
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 403
        assert "Email already registered" in response.text

    async def test_register_weak_password(self, client: AsyncTestClient) -> None:
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "weak",
            },
        )

        assert response.status_code == 403
        assert "Password" in response.text

    async def test_login_success(self, client: AsyncTestClient, test_user: User) -> None:
        response = await client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client: AsyncTestClient, test_user: User) -> None:
        response = await client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "WrongPassword",
            },
        )

        assert response.status_code == 403
        assert "Invalid credentials" in response.text

    async def test_login_nonexistent_user(self, client: AsyncTestClient) -> None:
        response = await client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "SomePassword123",
            },
        )

        assert response.status_code == 403
        assert "Invalid credentials" in response.text

    async def test_login_inactive_user(self, client: AsyncTestClient, db_session: AsyncSession) -> None:
        inactive_user = User(
            username="inactive",
            email="inactive@example.com",
            password_hash=password_service.hash_password("TestPassword123"),
            is_active=False,
        )
        db_session.add(inactive_user)
        await db_session.commit()

        response = await client.post(
            "/api/auth/login",
            json={
                "username": "inactive",
                "password": "TestPassword123",
            },
        )

        assert response.status_code == 403
        assert "Account is inactive" in response.text

    async def test_refresh_token_success(self, client: AsyncTestClient, test_user: User) -> None:
        login_response = await client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_token_invalid(self, client: AsyncTestClient) -> None:
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 403

    async def test_get_me_authenticated(self, client: AsyncTestClient, test_user: User) -> None:
        login_response = await client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123",
            },
        )
        access_token = login_response.json()["access_token"]

        response = await client.post(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"
        assert "id" in data

    async def test_get_me_unauthenticated(self, client: AsyncTestClient) -> None:
        response = await client.post("/api/auth/me")

        assert response.status_code == 401

    async def test_logout_authenticated(self, client: AsyncTestClient, test_user: User) -> None:
        login_response = await client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123",
            },
        )
        access_token = login_response.json()["access_token"]

        response = await client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]

    async def test_logout_unauthenticated(self, client: AsyncTestClient) -> None:
        response = await client.post("/api/auth/logout")

        assert response.status_code == 401

"""Authentication endpoints integration tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from litestar.testing import AsyncTestClient


@pytest.fixture(autouse=True)
async def _clean_db(truncate_tables: None) -> None:
    """Auto-truncate tables before each test for isolation."""


@pytest.fixture
async def registered_user(client: AsyncTestClient) -> dict:
    """Create a test user via the registration API."""
    response = await client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
class TestAuthEndpoints:
    async def test_register_success(self, client: AsyncTestClient) -> None:
        """Test user registration returns tokens."""
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

        me_response = await client.post(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["username"] == "newuser"
        assert user_data["email"] == "newuser@example.com"
        assert user_data["first_name"] == "New"

    async def test_register_duplicate_username(self, client: AsyncTestClient, registered_user: dict) -> None:
        """Test registration with existing username fails."""
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "different@example.com",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 403
        assert "Username already exists" in response.text

    async def test_register_duplicate_email(self, client: AsyncTestClient, registered_user: dict) -> None:
        """Test registration with existing email fails."""
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "differentuser",
                "email": "test@example.com",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 403
        assert "Email already registered" in response.text

    async def test_register_weak_password(self, client: AsyncTestClient) -> None:
        """Test registration with weak password fails validation."""
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "weak",
            },
        )

        assert response.status_code == 400

    async def test_login_success(self, client: AsyncTestClient, registered_user: dict) -> None:
        """Test login with valid credentials returns tokens."""
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

    async def test_login_invalid_credentials(self, client: AsyncTestClient, registered_user: dict) -> None:
        """Test login with wrong password fails."""
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
        """Test login with non-existent user fails."""
        response = await client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "SomePassword123",
            },
        )

        assert response.status_code == 403
        assert "Invalid credentials" in response.text

    async def test_refresh_token_success(self, client: AsyncTestClient, registered_user: dict) -> None:
        """Test refreshing tokens with valid refresh token."""
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
        """Test refreshing with invalid token fails."""
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 403

    async def test_get_me_authenticated(self, client: AsyncTestClient, registered_user: dict) -> None:
        """Test getting current user profile with valid token."""
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
        """Test getting profile without token fails."""
        response = await client.post("/api/auth/me")

        assert response.status_code == 401

    async def test_logout_authenticated(self, client: AsyncTestClient, registered_user: dict) -> None:
        """Test logout with valid token succeeds."""
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
        """Test logout without token fails."""
        response = await client.post("/api/auth/logout")

        assert response.status_code == 401

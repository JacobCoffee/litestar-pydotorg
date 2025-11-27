"""Tests for JWT token service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from jose import jwt

from pydotorg.config import settings
from pydotorg.core.auth.jwt import JWTService, jwt_service


class TestJWTServiceCreateAccessToken:
    """Test suite for JWTService.create_access_token."""

    def test_creates_valid_token(self) -> None:
        """Test that create_access_token generates a valid JWT."""
        user_id = uuid4()
        token = jwt_service.create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_user_id(self) -> None:
        """Test that token payload contains the user ID."""
        user_id = uuid4()
        token = jwt_service.create_access_token(user_id)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == str(user_id)

    def test_token_type_is_access(self) -> None:
        """Test that token type is 'access'."""
        user_id = uuid4()
        token = jwt_service.create_access_token(user_id)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["type"] == "access"

    def test_token_has_expiration(self) -> None:
        """Test that token has expiration claim."""
        user_id = uuid4()
        token = jwt_service.create_access_token(user_id)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert "exp" in payload
        assert payload["exp"] > datetime.now(UTC).timestamp()

    def test_custom_expiration(self) -> None:
        """Test that custom expiration delta is respected."""
        user_id = uuid4()
        expires_delta = timedelta(minutes=5)
        token = jwt_service.create_access_token(user_id, expires_delta=expires_delta)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        now = datetime.now(UTC)

        assert (exp_time - now).total_seconds() <= 5 * 60 + 5  # 5 minutes + buffer


class TestJWTServiceCreateRefreshToken:
    """Test suite for JWTService.create_refresh_token."""

    def test_creates_valid_token(self) -> None:
        """Test that create_refresh_token generates a valid JWT."""
        user_id = uuid4()
        token = jwt_service.create_refresh_token(user_id)

        assert token is not None
        assert isinstance(token, str)

    def test_token_type_is_refresh(self) -> None:
        """Test that token type is 'refresh'."""
        user_id = uuid4()
        token = jwt_service.create_refresh_token(user_id)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["type"] == "refresh"

    def test_refresh_token_has_longer_expiration(self) -> None:
        """Test that refresh token has longer expiration than access token."""
        user_id = uuid4()
        access_token = jwt_service.create_access_token(user_id)
        refresh_token = jwt_service.create_refresh_token(user_id)

        access_payload = jwt.decode(access_token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        refresh_payload = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.jwt_algorithm])

        assert refresh_payload["exp"] > access_payload["exp"]


class TestJWTServiceCreateVerificationToken:
    """Test suite for JWTService.create_verification_token."""

    def test_creates_valid_token(self) -> None:
        """Test that create_verification_token generates a valid JWT."""
        user_id = uuid4()
        email = "test@example.com"
        token = jwt_service.create_verification_token(user_id, email)

        assert token is not None
        assert isinstance(token, str)

    def test_token_type_is_verify_email(self) -> None:
        """Test that token type is 'verify_email'."""
        user_id = uuid4()
        email = "test@example.com"
        token = jwt_service.create_verification_token(user_id, email)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["type"] == "verify_email"

    def test_token_contains_email(self) -> None:
        """Test that token payload contains the email."""
        user_id = uuid4()
        email = "test@example.com"
        token = jwt_service.create_verification_token(user_id, email)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["email"] == email


class TestJWTServiceDecodeToken:
    """Test suite for JWTService.decode_token."""

    def test_decodes_valid_token(self) -> None:
        """Test that decode_token returns payload for valid token."""
        user_id = uuid4()
        token = jwt_service.create_access_token(user_id)

        payload = jwt_service.decode_token(token)
        assert payload["sub"] == str(user_id)

    def test_raises_on_invalid_token(self) -> None:
        """Test that decode_token raises ValueError for invalid token."""
        with pytest.raises(ValueError, match="Invalid token"):
            jwt_service.decode_token("invalid-token")

    def test_raises_on_expired_token(self) -> None:
        """Test that decode_token raises ValueError for expired token."""
        user_id = uuid4()
        token = jwt_service.create_access_token(user_id, expires_delta=timedelta(seconds=-1))

        with pytest.raises(ValueError, match="Invalid token"):
            jwt_service.decode_token(token)

    def test_raises_on_wrong_secret(self) -> None:
        """Test that decode_token raises ValueError for token with wrong secret."""
        user_id = uuid4()
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "type": "access",
        }
        token = jwt.encode(payload, "wrong-secret", algorithm=settings.jwt_algorithm)

        with pytest.raises(ValueError, match="Invalid token"):
            jwt_service.decode_token(token)


class TestJWTServiceVerifyTokenType:
    """Test suite for JWTService.verify_token_type."""

    def test_passes_for_matching_type(self) -> None:
        """Test that verify_token_type passes for matching type."""
        payload = {"type": "access"}
        jwt_service.verify_token_type(payload, "access")

    def test_raises_for_mismatched_type(self) -> None:
        """Test that verify_token_type raises for mismatched type."""
        payload = {"type": "access"}
        with pytest.raises(ValueError, match="Invalid token type"):
            jwt_service.verify_token_type(payload, "refresh")

    def test_raises_for_missing_type(self) -> None:
        """Test that verify_token_type raises for missing type."""
        payload = {}
        with pytest.raises(ValueError, match="Invalid token type"):
            jwt_service.verify_token_type(payload, "access")


class TestJWTServiceGetUserIdFromToken:
    """Test suite for JWTService.get_user_id_from_token."""

    def test_returns_user_id_from_access_token(self) -> None:
        """Test that get_user_id_from_token returns UUID from access token."""
        user_id = uuid4()
        token = jwt_service.create_access_token(user_id)

        result = jwt_service.get_user_id_from_token(token)
        assert result == user_id
        assert isinstance(result, UUID)

    def test_returns_user_id_from_refresh_token(self) -> None:
        """Test that get_user_id_from_token returns UUID from refresh token."""
        user_id = uuid4()
        token = jwt_service.create_refresh_token(user_id)

        result = jwt_service.get_user_id_from_token(token, token_type="refresh")
        assert result == user_id

    def test_raises_for_wrong_token_type(self) -> None:
        """Test that get_user_id_from_token raises for wrong token type."""
        user_id = uuid4()
        token = jwt_service.create_refresh_token(user_id)

        with pytest.raises(ValueError, match="Invalid token type"):
            jwt_service.get_user_id_from_token(token, token_type="access")

    def test_raises_for_missing_sub_claim(self) -> None:
        """Test that get_user_id_from_token raises for missing sub claim."""
        payload = {
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "type": "access",
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

        with pytest.raises(ValueError, match="Token does not contain user ID"):
            jwt_service.get_user_id_from_token(token)

    def test_raises_for_invalid_uuid(self) -> None:
        """Test that get_user_id_from_token raises for invalid UUID in sub."""
        payload = {
            "sub": "not-a-uuid",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "type": "access",
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

        with pytest.raises(ValueError, match="Invalid user ID in token"):
            jwt_service.get_user_id_from_token(token)


class TestJWTServiceInstance:
    """Test suite for jwt_service singleton."""

    def test_jwt_service_is_instance_of_jwtservice(self) -> None:
        """Test that jwt_service is a JWTService instance."""
        assert isinstance(jwt_service, JWTService)

    def test_jwt_service_is_singleton(self) -> None:
        """Test that jwt_service is the same instance."""
        from pydotorg.core.auth.jwt import jwt_service as jwt_service2

        assert jwt_service is jwt_service2

"""Authentication service unit tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from jose import jwt

from pydotorg.config import settings
from pydotorg.core.auth.jwt import jwt_service
from pydotorg.core.auth.password import password_service


class TestPasswordService:
    def test_hash_password(self) -> None:
        password = "TestPassword123"
        hashed = password_service.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_success(self) -> None:
        password = "TestPassword123"
        hashed = password_service.hash_password(password)

        assert password_service.verify_password(password, hashed) is True

    def test_verify_password_failure(self) -> None:
        password = "TestPassword123"
        hashed = password_service.hash_password(password)

        assert password_service.verify_password("WrongPassword", hashed) is False

    def test_validate_password_strength_too_short(self) -> None:
        is_valid, error = password_service.validate_password_strength("Short1")
        assert is_valid is False
        assert "at least 8 characters" in error

    def test_validate_password_strength_no_uppercase(self) -> None:
        is_valid, error = password_service.validate_password_strength("lowercase123")
        assert is_valid is False
        assert "uppercase letter" in error

    def test_validate_password_strength_no_lowercase(self) -> None:
        is_valid, error = password_service.validate_password_strength("UPPERCASE123")
        assert is_valid is False
        assert "lowercase letter" in error

    def test_validate_password_strength_no_digit(self) -> None:
        is_valid, error = password_service.validate_password_strength("NoDigits")
        assert is_valid is False
        assert "digit" in error

    def test_validate_password_strength_valid(self) -> None:
        is_valid, error = password_service.validate_password_strength("ValidPass123")
        assert is_valid is True
        assert error is None


class TestJWTService:
    def test_create_access_token(self) -> None:
        user_id = uuid4()
        token = jwt_service.create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    def test_create_refresh_token(self) -> None:
        user_id = uuid4()
        token = jwt_service.create_refresh_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_decode_token_valid(self) -> None:
        user_id = uuid4()
        token = jwt_service.create_access_token(user_id)

        payload = jwt_service.decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    def test_decode_token_invalid(self) -> None:
        with pytest.raises(ValueError, match="Invalid token"):
            jwt_service.decode_token("invalid.token.here")

    def test_decode_token_expired(self) -> None:
        user_id = uuid4()
        past_time = datetime.now(UTC) - timedelta(hours=1)
        payload = {
            "sub": str(user_id),
            "exp": past_time,
            "iat": past_time - timedelta(hours=2),
            "type": "access",
        }
        expired_token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

        with pytest.raises(ValueError, match="Invalid token"):
            jwt_service.decode_token(expired_token)

    def test_verify_token_type_valid(self) -> None:
        payload = {"type": "access", "sub": str(uuid4())}
        jwt_service.verify_token_type(payload, "access")

    def test_verify_token_type_invalid(self) -> None:
        payload = {"type": "refresh", "sub": str(uuid4())}
        with pytest.raises(ValueError, match="Invalid token type"):
            jwt_service.verify_token_type(payload, "access")

    def test_get_user_id_from_token(self) -> None:
        user_id = uuid4()
        token = jwt_service.create_access_token(user_id)

        extracted_id = jwt_service.get_user_id_from_token(token)
        assert extracted_id == user_id

    def test_get_user_id_from_token_wrong_type(self) -> None:
        user_id = uuid4()
        refresh_token = jwt_service.create_refresh_token(user_id)

        with pytest.raises(ValueError, match="Invalid token type"):
            jwt_service.get_user_id_from_token(refresh_token, token_type="access")

    def test_custom_expiration(self) -> None:
        user_id = uuid4()
        custom_delta = timedelta(minutes=30)
        token = jwt_service.create_access_token(user_id, expires_delta=custom_delta)

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        iat_time = datetime.fromtimestamp(payload["iat"], tz=UTC)

        time_diff = exp_time - iat_time
        assert 29 <= time_diff.total_seconds() / 60 <= 31

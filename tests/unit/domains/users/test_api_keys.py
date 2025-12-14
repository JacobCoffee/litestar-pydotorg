"""Unit tests for API key functionality."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pydotorg.domains.users.api_keys import API_KEY_BYTES, API_KEY_PREFIX, APIKey, APIKeyService


class TestAPIKeyModel:
    """Tests for the APIKey model."""

    def test_generate_key_returns_tuple(self) -> None:
        """Test that generate_key returns a tuple of (full_key, key_hash, key_prefix)."""
        full_key, key_hash, key_prefix = APIKey.generate_key()

        assert isinstance(full_key, str)
        assert isinstance(key_hash, str)
        assert isinstance(key_prefix, str)

    def test_generate_key_prefix_format(self) -> None:
        """Test that generated key starts with the correct prefix."""
        full_key, _, key_prefix = APIKey.generate_key()

        assert full_key.startswith(API_KEY_PREFIX)
        assert key_prefix == full_key[:12]
        assert key_prefix.startswith(API_KEY_PREFIX)

    def test_generate_key_hash_is_sha256(self) -> None:
        """Test that the key hash is a valid SHA-256 hash (64 hex chars)."""
        _, key_hash, _ = APIKey.generate_key()

        assert len(key_hash) == 64
        assert all(c in "0123456789abcdef" for c in key_hash)

    def test_generate_key_uniqueness(self) -> None:
        """Test that each generated key is unique."""
        keys = [APIKey.generate_key() for _ in range(10)]
        full_keys = [k[0] for k in keys]
        hashes = [k[1] for k in keys]

        assert len(set(full_keys)) == 10
        assert len(set(hashes)) == 10

    def test_hash_key_consistency(self) -> None:
        """Test that hashing the same key produces the same hash."""
        full_key, expected_hash, _ = APIKey.generate_key()
        computed_hash = APIKey.hash_key(full_key)

        assert computed_hash == expected_hash

    def test_hash_key_different_for_different_keys(self) -> None:
        """Test that different keys produce different hashes."""
        key1, _, _ = APIKey.generate_key()
        key2, _, _ = APIKey.generate_key()

        assert APIKey.hash_key(key1) != APIKey.hash_key(key2)

    def test_is_expired_false_when_no_expiry(self) -> None:
        """Test that is_expired returns False when expires_at is None."""
        api_key = APIKey(
            user_id=uuid4(),
            name="test",
            key_hash="abc123",
            key_prefix="pyorg_abc1",
            expires_at=None,
        )

        assert api_key.is_expired is False

    def test_is_expired_false_when_future_expiry(self) -> None:
        """Test that is_expired returns False when expires_at is in the future."""
        api_key = APIKey(
            user_id=uuid4(),
            name="test",
            key_hash="abc123",
            key_prefix="pyorg_abc1",
            expires_at=datetime.now(tz=UTC) + timedelta(days=1),
        )

        assert api_key.is_expired is False

    def test_is_expired_true_when_past_expiry(self) -> None:
        """Test that is_expired returns True when expires_at is in the past."""
        api_key = APIKey(
            user_id=uuid4(),
            name="test",
            key_hash="abc123",
            key_prefix="pyorg_abc1",
            expires_at=datetime.now(tz=UTC) - timedelta(days=1),
        )

        assert api_key.is_expired is True

    def test_is_valid_true_when_active_and_not_expired(self) -> None:
        """Test that is_valid returns True when key is active and not expired."""
        api_key = APIKey(
            user_id=uuid4(),
            name="test",
            key_hash="abc123",
            key_prefix="pyorg_abc1",
            is_active=True,
            expires_at=None,
        )

        assert api_key.is_valid is True

    def test_is_valid_false_when_inactive(self) -> None:
        """Test that is_valid returns False when key is inactive."""
        api_key = APIKey(
            user_id=uuid4(),
            name="test",
            key_hash="abc123",
            key_prefix="pyorg_abc1",
            is_active=False,
            expires_at=None,
        )

        assert api_key.is_valid is False

    def test_is_valid_false_when_expired(self) -> None:
        """Test that is_valid returns False when key is expired."""
        api_key = APIKey(
            user_id=uuid4(),
            name="test",
            key_hash="abc123",
            key_prefix="pyorg_abc1",
            is_active=True,
            expires_at=datetime.now(tz=UTC) - timedelta(days=1),
        )

        assert api_key.is_valid is False


class TestAPIKeyServiceStatic:
    """Tests for APIKeyService static methods."""

    def test_create_key_returns_api_key_and_raw_key(self) -> None:
        """Test that create_key returns an APIKey instance and raw key string."""
        user_id = uuid4()
        api_key, raw_key = APIKeyService.create_key(
            user_id=user_id,
            name="Test Key",
            description="A test key",
        )

        assert isinstance(api_key, APIKey)
        assert isinstance(raw_key, str)
        assert api_key.user_id == user_id
        assert api_key.name == "Test Key"
        assert api_key.description == "A test key"
        assert raw_key.startswith(API_KEY_PREFIX)

    def test_create_key_with_expiration(self) -> None:
        """Test that create_key correctly sets expiration date."""
        user_id = uuid4()
        api_key, _ = APIKeyService.create_key(
            user_id=user_id,
            name="Expiring Key",
            expires_in_days=30,
        )

        assert api_key.expires_at is not None
        expected = datetime.now(tz=UTC) + timedelta(days=30)
        assert abs((api_key.expires_at - expected).total_seconds()) < 5

    def test_create_key_without_expiration(self) -> None:
        """Test that create_key returns None expires_at when not specified."""
        user_id = uuid4()
        api_key, _ = APIKeyService.create_key(
            user_id=user_id,
            name="Non-expiring Key",
        )

        assert api_key.expires_at is None

    def test_validate_key_success(self) -> None:
        """Test that validate_key returns True for valid key."""
        user_id = uuid4()
        api_key, raw_key = APIKeyService.create_key(
            user_id=user_id,
            name="Valid Key",
        )
        api_key.is_active = True

        assert APIKeyService.validate_key(raw_key, api_key) is True

    def test_validate_key_wrong_key(self) -> None:
        """Test that validate_key returns False for wrong key."""
        user_id = uuid4()
        api_key, _ = APIKeyService.create_key(
            user_id=user_id,
            name="Valid Key",
        )
        api_key.is_active = True

        assert APIKeyService.validate_key("pyorg_wrongkey123456", api_key) is False

    def test_validate_key_inactive(self) -> None:
        """Test that validate_key returns False for inactive key."""
        user_id = uuid4()
        api_key, raw_key = APIKeyService.create_key(
            user_id=user_id,
            name="Inactive Key",
        )
        api_key.is_active = False

        assert APIKeyService.validate_key(raw_key, api_key) is False

    def test_validate_key_expired(self) -> None:
        """Test that validate_key returns False for expired key."""
        user_id = uuid4()
        api_key, raw_key = APIKeyService.create_key(
            user_id=user_id,
            name="Expired Key",
        )
        api_key.is_active = True
        api_key.expires_at = datetime.now(tz=UTC) - timedelta(days=1)

        assert APIKeyService.validate_key(raw_key, api_key) is False


class TestAPIKeyConstants:
    """Tests for API key constants."""

    def test_api_key_prefix(self) -> None:
        """Test that API_KEY_PREFIX is set correctly."""
        assert API_KEY_PREFIX == "pyorg_"

    def test_api_key_bytes(self) -> None:
        """Test that API_KEY_BYTES is a reasonable value."""
        assert API_KEY_BYTES == 32
        assert API_KEY_BYTES >= 16

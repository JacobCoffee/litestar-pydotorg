"""API Key model and service for API authentication."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003 - UUID needed at runtime for SQLAlchemy Mapped annotation

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydotorg.core.database.base import AuditBase

if TYPE_CHECKING:
    from pydotorg.domains.users.models import User

API_KEY_PREFIX = "pyorg_"
API_KEY_BYTES = 32


class APIKey(AuditBase):
    """API key for programmatic access to the API.

    Keys are stored as SHA-256 hashes for security.
    The actual key is only shown once at creation time.
    """

    __tablename__ = "api_keys"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(12), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship("User", lazy="selectin")

    @property
    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(tz=UTC) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        """Generate a new API key.

        Returns:
            Tuple of (full_key, key_hash, key_prefix)
        """
        key_suffix = secrets.token_urlsafe(API_KEY_BYTES)
        full_key = f"{API_KEY_PREFIX}{key_suffix}"
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        key_prefix = full_key[:12]
        return full_key, key_hash, key_prefix

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for comparison.

        Args:
            key: The raw API key.

        Returns:
            SHA-256 hash of the key.
        """
        return hashlib.sha256(key.encode()).hexdigest()


class APIKeyService:
    """Service for managing API keys."""

    @staticmethod
    def create_key(
        user_id: UUID,
        name: str,
        description: str = "",
        expires_in_days: int | None = None,
    ) -> tuple[APIKey, str]:
        """Create a new API key for a user.

        Args:
            user_id: The user ID to create the key for.
            name: A name/label for the key.
            description: Optional description.
            expires_in_days: Optional expiration in days.

        Returns:
            Tuple of (APIKey instance, raw key string).
            The raw key is only available at creation time.
        """
        full_key, key_hash, key_prefix = APIKey.generate_key()

        expires_at = None
        if expires_in_days is not None:
            expires_at = datetime.now(tz=UTC) + timedelta(days=expires_in_days)

        api_key = APIKey(
            user_id=user_id,
            name=name,
            description=description,
            key_hash=key_hash,
            key_prefix=key_prefix,
            expires_at=expires_at,
        )

        return api_key, full_key

    @staticmethod
    def validate_key(key: str, stored_key: APIKey) -> bool:
        """Validate an API key against a stored key.

        Args:
            key: The raw API key to validate.
            stored_key: The stored APIKey instance.

        Returns:
            True if the key is valid, False otherwise.
        """
        if not stored_key.is_valid:
            return False

        key_hash = APIKey.hash_key(key)
        return secrets.compare_digest(key_hash, stored_key.key_hash)

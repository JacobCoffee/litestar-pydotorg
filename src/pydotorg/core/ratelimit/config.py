"""Rate limiting configuration for API endpoints."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RateLimitTier(str, Enum):
    """Rate limit tier levels with corresponding limits."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RateLimitConfig(BaseSettings):
    """Rate limiting configuration with tiered limits and multipliers."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RATELIMIT_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    critical_limit: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Requests per minute for CRITICAL tier (auth endpoints, password reset)",
    )
    high_limit: int = Field(
        default=20,
        ge=1,
        le=500,
        description="Requests per minute for HIGH tier (user mutations, content creation)",
    )
    medium_limit: int = Field(
        default=60,
        ge=1,
        le=1000,
        description="Requests per minute for MEDIUM tier (standard API endpoints)",
    )
    low_limit: int = Field(
        default=120,
        ge=1,
        le=5000,
        description="Requests per minute for LOW tier (read-only, public content)",
    )

    authenticated_multiplier: float = Field(
        default=4.0,
        ge=1.0,
        le=10.0,
        description="Multiplier for authenticated users (4x default limits)",
    )
    staff_multiplier: float = Field(
        default=5.0,
        ge=1.0,
        le=20.0,
        description="Additional multiplier for staff users (5x on top of authenticated)",
    )

    enabled: bool = Field(
        default=True,
        description="Global rate limiting toggle",
    )
    redis_key_prefix: str = Field(
        default="ratelimit:",
        description="Redis key prefix for rate limit storage",
    )
    window_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Time window for rate limiting in seconds",
    )

    def get_limit(self, tier: RateLimitTier, *, is_authenticated: bool = False, is_staff: bool = False) -> int:
        """Calculate rate limit based on tier and user status.

        Args:
            tier: Rate limit tier level
            is_authenticated: Whether user is authenticated
            is_staff: Whether user is staff

        Returns:
            Calculated rate limit per minute
        """
        base_limits = {
            RateLimitTier.CRITICAL: self.critical_limit,
            RateLimitTier.HIGH: self.high_limit,
            RateLimitTier.MEDIUM: self.medium_limit,
            RateLimitTier.LOW: self.low_limit,
        }

        limit = base_limits[tier]

        if is_authenticated:
            limit = int(limit * self.authenticated_multiplier)

        if is_staff:
            limit = int(limit * self.staff_multiplier)

        return limit

    def get_tier_limits(self) -> dict[str, dict[str, int]]:
        """Get all tier limits for different user types.

        Returns:
            Dictionary mapping tier names to limits for anonymous, authenticated, and staff users
        """
        return {
            tier.value: {
                "anonymous": self.get_limit(tier),
                "authenticated": self.get_limit(tier, is_authenticated=True),
                "staff": self.get_limit(tier, is_authenticated=True, is_staff=True),
            }
            for tier in RateLimitTier
        }


@lru_cache
def get_ratelimit_config() -> RateLimitConfig:
    """Get cached rate limit configuration instance.

    Returns:
        RateLimitConfig instance
    """
    return RateLimitConfig()


ratelimit_config = get_ratelimit_config()

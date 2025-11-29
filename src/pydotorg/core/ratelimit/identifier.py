"""Rate limit identifier for user-aware rate limiting."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litestar.connection import Request

    from pydotorg.domains.users.models import User


async def get_rate_limit_identifier(request: Request) -> str:
    """Generate a rate limit identifier based on user authentication status.

    Returns different identifier prefixes based on user role:
    - `admin:{user_id}` for staff or superuser accounts
    - `user:{user_id}` for authenticated regular users
    - `anon:{ip_address}` for anonymous/unauthenticated users

    The identifier is used to track rate limits per user/IP, allowing
    different rate limit configurations for different user types.

    Args:
        request: The incoming Litestar request object. User is populated by
                UserPopulationMiddleware if authenticated.

    Returns:
        String identifier in format `prefix:value` for rate limit tracking.

    Example:
        >>> # Authenticated staff user
        >>> identifier = await get_rate_limit_identifier(request)
        >>> # Returns: "admin:550e8400-e29b-41d4-a716-446655440000"

        >>> # Regular authenticated user
        >>> identifier = await get_rate_limit_identifier(request)
        >>> # Returns: "user:123e4567-e89b-12d3-a456-426614174000"

        >>> # Anonymous user from IP 192.168.1.1
        >>> identifier = await get_rate_limit_identifier(request)
        >>> # Returns: "anon:192.168.1.1"
    """
    user: User | None = request.scope.get("user")

    if user:
        if user.is_staff or user.is_superuser:
            return f"admin:{user.id}"
        return f"user:{user.id}"

    ip_address = _get_client_ip(request)
    return f"anon:{ip_address}"


def _get_client_ip(request: Request) -> str:
    """Extract client IP address from request with reverse proxy support.

    Checks X-Forwarded-For header first (for reverse proxy setups),
    then falls back to direct client connection.

    Args:
        request: The incoming Litestar request object.

    Returns:
        Client IP address as string. Returns "unknown" if no client info available.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    client = request.scope.get("client")
    if client:
        return client[0]

    return "unknown"

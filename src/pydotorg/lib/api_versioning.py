"""API versioning middleware with version negotiation support.

Provides version negotiation via Accept header, URL path, and query parameters.
Includes deprecation warnings for old API versions.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from litestar.middleware import MiddlewareProtocol

if TYPE_CHECKING:
    from datetime import date

    from litestar.types import ASGIApp, Message, Receive, Scope, Send

_MIN_PARTS_FOR_PATCH = 2


@dataclass(frozen=True)
class APIVersion:
    """Represents an API version with deprecation metadata."""

    major: int
    minor: int
    patch: int = 0
    deprecated: bool = False
    sunset_date: date | None = None

    @classmethod
    def from_string(cls, version_str: str) -> APIVersion:
        """Parse version from string like 'v1' or '1.2.3'.

        Args:
            version_str: Version string in format 'v1', '1', '1.2', or '1.2.3'

        Returns:
            Parsed APIVersion instance

        Raises:
            ValueError: If version string is invalid
        """
        version_str = version_str.strip().lower()
        version_str = version_str.removeprefix("v")

        parts = version_str.split(".")
        if not parts or not parts[0].isdigit():
            msg = f"Invalid version string: {version_str}"
            raise ValueError(msg)

        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        patch = int(parts[2]) if len(parts) > _MIN_PARTS_FOR_PATCH and parts[2].isdigit() else 0

        return cls(major=major, minor=minor, patch=patch)

    def __str__(self) -> str:
        """Return version as string (e.g., 'v1.0.0')."""
        return f"v{self.major}.{self.minor}.{self.patch}"

    def to_short_string(self) -> str:
        """Return short version string (e.g., 'v1')."""
        return f"v{self.major}"

    def __lt__(self, other: APIVersion) -> bool:
        """Compare versions for sorting."""
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __eq__(self, other: object) -> bool:
        """Compare versions for equality."""
        if not isinstance(other, APIVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __hash__(self) -> int:
        """Return hash for use in sets and dicts."""
        return hash((self.major, self.minor, self.patch))


class APIVersionRegistry:
    """Registry of supported API versions with deprecation metadata."""

    def __init__(self) -> None:
        """Initialize the version registry with default versions."""
        self._versions: dict[int, APIVersion] = {}
        self._default_version: APIVersion | None = None
        self._register_default_versions()

    def _register_default_versions(self) -> None:
        """Register the default supported API versions."""
        v1 = APIVersion(major=1, minor=0, patch=0)
        self.register(v1, is_default=True)

    def register(
        self,
        version: APIVersion,
        *,
        is_default: bool = False,
    ) -> None:
        """Register a new API version.

        Args:
            version: The version to register (with deprecation metadata already set)
            is_default: Whether this should be the default version
        """
        self._versions[version.major] = version

        if is_default or self._default_version is None:
            self._default_version = version

    def get_version(self, major: int) -> APIVersion | None:
        """Get a version by major version number.

        Args:
            major: The major version number

        Returns:
            The APIVersion if found, None otherwise
        """
        return self._versions.get(major)

    def get_default(self) -> APIVersion:
        """Get the default API version.

        Returns:
            The default APIVersion

        Raises:
            RuntimeError: If no default version is set
        """
        if self._default_version is None:
            msg = "No default API version configured"
            raise RuntimeError(msg)
        return self._default_version

    def is_supported(self, version: APIVersion) -> bool:
        """Check if a version is supported.

        Args:
            version: The version to check

        Returns:
            True if the version is supported, False otherwise
        """
        return version.major in self._versions


registry = APIVersionRegistry()


class APIVersionMiddleware(MiddlewareProtocol):
    """Middleware that negotiates API version and adds version headers.

    Version negotiation order:
    1. Accept header (application/vnd.pydotorg.v1+json)
    2. URL path prefix (/api/v1/...)
    3. Query parameter (?api_version=1)
    4. Default version (v1)

    Adds response headers:
    - X-API-Version: Current version used
    - X-API-Deprecated: true/false
    - X-API-Sunset-Date: ISO date if deprecated
    """

    ACCEPT_PATTERN = re.compile(r"application/vnd\.pydotorg\.v(\d+)\+json")
    PATH_PATTERN = re.compile(r"^/api/v(\d+)/")

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process the request and add version headers to response.

        Args:
            scope: The ASGI scope
            receive: The receive callable
            send: The send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        version = self._negotiate_version(scope)
        scope["api_version"] = version

        async def send_with_version_headers(message: Message) -> None:
            """Add version headers to the response.

            Args:
                message: The ASGI message
            """
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"X-API-Version", str(version).encode()))

                if version.deprecated:
                    headers.append((b"X-API-Deprecated", b"true"))
                    if version.sunset_date:
                        sunset_str = version.sunset_date.isoformat()
                        headers.append((b"X-API-Sunset-Date", sunset_str.encode()))

                        deprecation_info = {
                            "deprecated": True,
                            "sunset_date": sunset_str,
                            "message": f"API version {version} is deprecated and will be removed on {sunset_str}",
                            "current_version": str(registry.get_default()),
                        }
                        headers.append((b"X-API-Deprecation-Info", json.dumps(deprecation_info).encode()))
                else:
                    headers.append((b"X-API-Deprecated", b"false"))

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_with_version_headers)

    def _negotiate_version(self, scope: Scope) -> APIVersion:
        """Negotiate API version from request.

        Checks in order:
        1. Accept header
        2. URL path
        3. Query parameter
        4. Default version

        Args:
            scope: The ASGI scope

        Returns:
            The negotiated APIVersion
        """
        accept_version = self._extract_version_from_accept(scope)
        if accept_version and registry.is_supported(accept_version):
            return registry.get_version(accept_version.major) or registry.get_default()

        path_version = self._extract_version_from_path(scope)
        if path_version and registry.is_supported(path_version):
            return registry.get_version(path_version.major) or registry.get_default()

        query_version = self._extract_version_from_query(scope)
        if query_version and registry.is_supported(query_version):
            return registry.get_version(query_version.major) or registry.get_default()

        return registry.get_default()

    def _extract_version_from_accept(self, scope: Scope) -> APIVersion | None:
        """Extract version from Accept header.

        Looks for: application/vnd.pydotorg.v1+json

        Args:
            scope: The ASGI scope

        Returns:
            APIVersion if found and valid, None otherwise
        """
        headers_dict = dict(scope.get("headers", []))
        accept_header = headers_dict.get(b"accept", b"").decode()

        match = self.ACCEPT_PATTERN.search(accept_header)
        if match:
            try:
                return APIVersion.from_string(match.group(1))
            except ValueError:
                pass

        return None

    def _extract_version_from_path(self, scope: Scope) -> APIVersion | None:
        """Extract version from URL path.

        Looks for: /api/v1/...

        Args:
            scope: The ASGI scope

        Returns:
            APIVersion if found and valid, None otherwise
        """
        path = scope.get("path", "")
        match = self.PATH_PATTERN.search(path)
        if match:
            try:
                return APIVersion.from_string(match.group(1))
            except ValueError:
                pass

        return None

    def _extract_version_from_query(self, scope: Scope) -> APIVersion | None:
        """Extract version from query parameter.

        Looks for: ?api_version=1

        Args:
            scope: The ASGI scope

        Returns:
            APIVersion if found and valid, None otherwise
        """
        query_string = scope.get("query_string", b"").decode()
        if not query_string:
            return None

        params = dict(param.split("=") for param in query_string.split("&") if "=" in param)
        version_str = params.get("api_version")

        if version_str:
            try:
                return APIVersion.from_string(version_str)
            except ValueError:
                pass

        return None


def deprecate_version(major: int, sunset_date: date | None = None) -> None:
    """Mark an API version as deprecated.

    Args:
        major: The major version number to deprecate
        sunset_date: Optional sunset date when version will be removed

    Example:
        >>> from datetime import date
        >>> deprecate_version(1, sunset_date=date(2025, 12, 31))
    """
    version = registry.get_version(major)
    if version:
        deprecated_version = APIVersion(
            major=version.major,
            minor=version.minor,
            patch=version.patch,
            deprecated=True,
            sunset_date=sunset_date,
        )
        registry.register(deprecated_version, is_default=(registry.get_default() == version))


def add_version(major: int, minor: int = 0, patch: int = 0, *, is_default: bool = False) -> APIVersion:
    """Add a new API version to the registry.

    Args:
        major: Major version number
        minor: Minor version number (default: 0)
        patch: Patch version number (default: 0)
        is_default: Whether this should be the default version

    Returns:
        The created APIVersion

    Example:
        >>> add_version(2, 0, 0, is_default=True)
        APIVersion(major=2, minor=0, patch=0)
    """
    version = APIVersion(major=major, minor=minor, patch=patch)
    registry.register(version, is_default=is_default)
    return version

# Authentication Recipes

Common authentication patterns and implementations for litestar-pydotorg.

## Protect an Endpoint

### Require Any Authenticated User

```python
from litestar import get
from pydotorg.core.guards import require_authenticated
from pydotorg.domains.users.models import User

@get("/profile", guards=[require_authenticated])
async def get_profile(current_user: User) -> dict:
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
    }
```

### Require Staff Access

```python
from litestar import get
from pydotorg.core.guards import require_staff

@get("/admin/users", guards=[require_staff])
async def list_all_users(db_session: AsyncSession) -> list[dict]:
    # Only staff can access this endpoint
    ...
```

### Require Admin Access

```python
from litestar import delete
from pydotorg.core.guards import require_admin

@delete("/admin/users/{user_id}", guards=[require_admin])
async def delete_user(user_id: UUID) -> None:
    # Only superusers can access this endpoint
    ...
```

### Require PSF Membership

```python
from litestar import get
from pydotorg.core.guards import require_membership

@get("/members/vote", guards=[require_membership])
async def vote_page(current_user: User) -> dict:
    # Only PSF members can access
    ...
```

## Custom Guards

### Owner-Only Guard

```python
from litestar import Request
from litestar.connection import ASGIConnection
from litestar.handlers import BaseRouteHandler
from litestar.exceptions import PermissionDeniedException


def require_owner(
    connection: ASGIConnection,
    route_handler: BaseRouteHandler,
) -> None:
    """Guard that requires the user to own the resource."""
    user = connection.user
    if not user:
        raise PermissionDeniedException("Authentication required")

    # Get resource ID from path
    resource_id = connection.path_params.get("product_id")
    if not resource_id:
        return

    # Check ownership (this would need async handling in practice)
    # For simple cases, you might store ownership in the request state
    owner_id = connection.scope.get("resource_owner_id")
    if owner_id and owner_id != user.id:
        raise PermissionDeniedException("You don't own this resource")


# Usage
@get("/{product_id}", guards=[require_owner])
async def get_my_product(product_id: UUID, current_user: User) -> dict:
    ...
```

### Rate-Limited Guard

```python
from litestar.exceptions import TooManyRequestsException
import time

# Simple in-memory rate limiter (use Redis in production)
request_counts: dict[str, list[float]] = {}

def rate_limit(max_requests: int = 10, window: int = 60):
    """Create a rate limiting guard."""

    def guard(
        connection: ASGIConnection,
        route_handler: BaseRouteHandler,
    ) -> None:
        user_id = str(connection.user.id) if connection.user else connection.client[0]
        now = time.time()

        if user_id not in request_counts:
            request_counts[user_id] = []

        # Clean old requests
        request_counts[user_id] = [
            t for t in request_counts[user_id]
            if now - t < window
        ]

        if len(request_counts[user_id]) >= max_requests:
            raise TooManyRequestsException("Rate limit exceeded")

        request_counts[user_id].append(now)

    return guard


# Usage
@post("/submit", guards=[rate_limit(max_requests=5, window=60)])
async def submit_form(data: FormData) -> dict:
    ...
```

## API Key Authentication

### API Key Model

```python
# models.py
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class APIKey(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "api_keys"

    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="api_keys")
```

### API Key Authentication Middleware

```python
from litestar.middleware import AbstractMiddleware
from litestar.types import ASGIApp, Receive, Scope, Send
import hashlib

class APIKeyMiddleware(AbstractMiddleware):
    """Middleware to authenticate API key requests."""

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        api_key = request.headers.get("X-API-Key")

        if api_key:
            # Hash the key for lookup
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Look up user by API key
            async with get_session() as session:
                result = await session.execute(
                    select(APIKey)
                    .where(APIKey.key == key_hash)
                    .where(APIKey.is_active == True)
                )
                api_key_obj = result.scalar_one_or_none()

                if api_key_obj:
                    scope["user"] = api_key_obj.user

        await self.app(scope, receive, send)
```

### Generate API Key

```python
import secrets
import hashlib

def generate_api_key() -> tuple[str, str]:
    """Generate an API key and its hash."""
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_hash


@post("/api-keys")
async def create_api_key(
    db_session: AsyncSession,
    current_user: User,
    name: str,
) -> dict:
    raw_key, key_hash = generate_api_key()

    api_key = APIKey(
        key=key_hash,
        name=name,
        user_id=current_user.id,
    )
    db_session.add(api_key)
    await db_session.commit()

    # Return raw key only once - user must save it
    return {
        "api_key": raw_key,
        "name": name,
        "warning": "Save this key - it won't be shown again",
    }
```

## OAuth Integration

### Link OAuth Account to Existing User

```python
@get("/oauth/{provider}/link")
async def link_oauth_account(
    provider: str,
    current_user: User,
    request: Request,
) -> RedirectResponse:
    """Start OAuth flow to link a new provider."""
    # Store user ID in session for callback
    request.session["linking_user_id"] = str(current_user.id)

    # Generate OAuth URL
    oauth_url = generate_oauth_url(provider)
    return RedirectResponse(url=oauth_url)


@get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    request: Request,
    db_session: AsyncSession,
) -> dict:
    """Handle OAuth callback."""
    # Check if linking to existing account
    linking_user_id = request.session.pop("linking_user_id", None)

    oauth_data = await exchange_oauth_code(provider, code)

    if linking_user_id:
        # Link to existing account
        user = await db_session.get(User, UUID(linking_user_id))
        user.oauth_provider = provider
        user.oauth_id = oauth_data["id"]
        await db_session.commit()
        return {"message": f"{provider} account linked"}

    # Normal OAuth login/registration
    ...
```

### Unlink OAuth Account

```python
@post("/oauth/{provider}/unlink")
async def unlink_oauth_account(
    provider: str,
    current_user: User,
    db_session: AsyncSession,
) -> dict:
    """Unlink an OAuth provider from account."""
    if current_user.oauth_provider != provider:
        raise NotFoundException("OAuth provider not linked")

    # Ensure user has a password before unlinking
    if not current_user.password_hash:
        raise ValidationException(
            "Set a password before unlinking OAuth"
        )

    current_user.oauth_provider = None
    current_user.oauth_id = None
    await db_session.commit()

    return {"message": f"{provider} account unlinked"}
```

## Two-Factor Authentication

### TOTP Setup

```python
import pyotp
import qrcode
import io
import base64

@post("/2fa/enable")
async def enable_2fa(
    current_user: User,
    db_session: AsyncSession,
) -> dict:
    """Enable 2FA for user."""
    # Generate secret
    secret = pyotp.random_base32()

    # Store secret (encrypted in production)
    current_user.totp_secret = secret
    await db_session.commit()

    # Generate QR code
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        current_user.email,
        issuer_name="Python.org"
    )

    qr = qrcode.make(uri)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_base64}",
    }


@post("/2fa/verify")
async def verify_2fa(
    code: str,
    current_user: User,
    db_session: AsyncSession,
) -> dict:
    """Verify 2FA code and activate."""
    if not current_user.totp_secret:
        raise ValidationException("2FA not set up")

    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(code):
        raise ValidationException("Invalid code")

    current_user.totp_enabled = True
    await db_session.commit()

    return {"message": "2FA enabled"}
```

### 2FA Login Flow

```python
@post("/auth/login")
async def login(
    credentials: LoginCredentials,
    db_session: AsyncSession,
    request: Request,
) -> dict:
    user = await authenticate_user(
        db_session,
        credentials.username,
        credentials.password,
    )

    if user.totp_enabled:
        # Store partial auth in session
        request.session["partial_auth_user_id"] = str(user.id)
        return {"requires_2fa": True}

    # Generate tokens
    tokens = generate_tokens(user)
    return tokens


@post("/auth/login/2fa")
async def login_2fa(
    code: str,
    request: Request,
    db_session: AsyncSession,
) -> dict:
    user_id = request.session.pop("partial_auth_user_id", None)
    if not user_id:
        raise ValidationException("No pending 2FA verification")

    user = await db_session.get(User, UUID(user_id))
    if not user or not user.totp_secret:
        raise ValidationException("Invalid state")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code):
        raise ValidationException("Invalid code")

    # Generate tokens
    tokens = generate_tokens(user)
    return tokens
```

## Session Management

### List Active Sessions

```python
@get("/sessions")
async def list_sessions(
    current_user: User,
    redis: Redis,
) -> list[dict]:
    """List all active sessions for user."""
    pattern = f"session:{current_user.id}:*"
    sessions = []

    async for key in redis.scan_iter(pattern):
        data = await redis.hgetall(key)
        sessions.append({
            "id": key.split(":")[-1],
            "created_at": data.get("created_at"),
            "last_active": data.get("last_active"),
            "ip_address": data.get("ip_address"),
            "user_agent": data.get("user_agent"),
        })

    return sessions


@delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: User,
    redis: Redis,
) -> dict:
    """Revoke a specific session."""
    key = f"session:{current_user.id}:{session_id}"
    deleted = await redis.delete(key)

    if not deleted:
        raise NotFoundException("Session not found")

    return {"message": "Session revoked"}


@delete("/sessions")
async def revoke_all_sessions(
    current_user: User,
    redis: Redis,
    request: Request,
) -> dict:
    """Revoke all sessions except current."""
    current_session = request.session.get("session_id")
    pattern = f"session:{current_user.id}:*"

    async for key in redis.scan_iter(pattern):
        if current_session and key.endswith(current_session):
            continue
        await redis.delete(key)

    return {"message": "All other sessions revoked"}
```

## See Also

- [API Usage Guide](../guides/api-usage.md) - Using authentication in API calls
- [Authentication Guide](../guides/authentication.md) - Full authentication documentation
- [Domain Patterns](domain-patterns.md) - Creating protected domain controllers

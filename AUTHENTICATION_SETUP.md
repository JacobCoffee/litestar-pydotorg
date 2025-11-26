# Authentication System Setup Guide

## Overview

This guide explains how to integrate the JWT-based authentication system into your Litestar application.

## Architecture

The authentication system consists of:

1. **Password Service** (`core/auth/password.py`): Bcrypt-based password hashing and validation
2. **JWT Service** (`core/auth/jwt.py`): Token creation and validation
3. **Middleware** (`core/auth/middleware.py`): Request authentication
4. **Guards** (`core/auth/guards.py`): Route-level authorization
5. **Auth Controller** (`domains/users/auth_controller.py`): Authentication endpoints

## Integration Steps

### 1. Update main.py

```python
from litestar import Litestar
from litestar.middleware import DefineMiddleware

from pydotorg.core.auth import JWTAuthMiddleware
from pydotorg.domains.users.auth_controller import AuthController

app = Litestar(
    route_handlers=[
        # ... existing handlers
        AuthController,  # Add auth endpoints
    ],
    middleware=[
        DefineMiddleware(JWTAuthMiddleware),  # Add JWT middleware
    ],
    # ... rest of config
)
```

### 2. Update Configuration

Ensure your `.env` file has these settings:

```env
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=10080  # 7 days
```

### 3. Database Migration

The User model already has `password_hash` field. If you need to migrate existing users:

```bash
uv run alembic revision --autogenerate -m "add auth fields"
uv run alembic upgrade head
```

## API Endpoints

### POST /api/auth/register

Register a new user.

**Request:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

### POST /api/auth/login

Authenticate an existing user.

**Request:**
```json
{
  "username": "johndoe",
  "password": "SecurePass123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

### POST /api/auth/refresh

Get new access and refresh tokens.

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

### POST /api/auth/me

Get current user information (requires authentication).

**Headers:**
```
Authorization: Bearer eyJhbGc...
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "date_joined": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T15:45:00Z",
  "has_membership": false
}
```

### POST /api/auth/logout

Logout (requires authentication).

**Headers:**
```
Authorization: Bearer eyJhbGc...
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

## Using Guards on Routes

### Example 1: Require Authentication

```python
from litestar import Controller, get
from pydotorg.core.auth import require_authenticated

class ProtectedController(Controller):
    path = "/api/protected"
    guards = [require_authenticated]

    @get("/")
    async def protected_route(self) -> dict[str, str]:
        return {"message": "This route requires authentication"}
```

### Example 2: Require Staff Privileges

```python
from litestar import Controller, get
from pydotorg.core.auth import require_staff
from pydotorg.domains.users.models import User

class AdminController(Controller):
    path = "/api/admin"
    guards = [require_staff]

    @get("/users")
    async def list_users(self, current_user: User) -> list[dict]:
        # current_user is automatically injected and guaranteed to be staff
        return [{"message": "Admin only"}]
```

### Example 3: Require PSF Membership

```python
from litestar import Controller, post
from pydotorg.core.auth import require_membership
from pydotorg.domains.users.models import User

class MemberController(Controller):
    path = "/api/members"
    guards = [require_membership]

    @post("/vote")
    async def cast_vote(self, current_user: User) -> dict:
        # Only PSF members can access this
        return {"message": "Vote recorded"}
```

### Available Guards

1. `require_authenticated` - User must be logged in
2. `require_staff` - User must have `is_staff=True`
3. `require_admin` - User must have `is_superuser=True`
4. `require_membership` - User must be a PSF member
5. `require_higher_membership` - User must be a non-basic PSF member

## Accessing Current User

In any authenticated route, you can access the current user:

```python
from litestar import get
from litestar.di import Provide
from pydotorg.core.auth import require_authenticated
from pydotorg.domains.users.models import User

async def get_current_user(request: Request) -> User:
    return request.user

@get("/profile", guards=[require_authenticated], dependencies={"current_user": Provide(get_current_user)})
async def get_profile(current_user: User) -> dict:
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
    }
```

## Client-Side Usage

### Using Bearer Token in Header

```javascript
const token = localStorage.getItem('access_token');

fetch('/api/auth/me', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

### Using Cookie

The middleware also supports cookie-based authentication:

```javascript
// Set cookie after login
document.cookie = `access_token=${token}; path=/; secure; samesite=strict`;

// Then requests work automatically
fetch('/api/auth/me')
```

## Security Best Practices

1. **Use HTTPS in Production**: Always use HTTPS to protect tokens in transit
2. **Store Tokens Securely**: Use httpOnly cookies or secure storage
3. **Short Access Token Lifetime**: Keep access tokens short-lived
4. **Implement Token Refresh**: Use refresh tokens to get new access tokens
5. **Logout Mechanism**: Clear tokens on client-side when user logs out
6. **Rate Limiting**: Add rate limiting to auth endpoints
7. **Password Requirements**: Enforce strong passwords (already implemented)

## Testing

Run authentication tests:

```bash
# Unit tests
uv run pytest tests/unit/test_auth.py -v

# Integration tests
uv run pytest tests/integration/test_auth_endpoints.py -v

# All tests
uv run pytest -v
```

## Error Handling

The system uses standard Litestar exceptions:

- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: User not found
- `409 Conflict`: Username/email already exists (in registration)

## Customization

### Custom Token Expiration

```python
from datetime import timedelta
from pydotorg.core.auth import jwt_service

# Create token with custom expiration
token = jwt_service.create_access_token(
    user_id=user.id,
    expires_delta=timedelta(hours=1)
)
```

### Custom Password Validation

Modify `core/auth/password.py`:

```python
@staticmethod
def validate_password_strength(password: str) -> tuple[bool, str | None]:
    # Add custom validation logic
    if "password" in password.lower():
        return False, "Password cannot contain the word 'password'"

    # ... existing validation
```

## Troubleshooting

### "Invalid token" Error

- Check if token has expired
- Verify SECRET_KEY matches between token creation and validation
- Ensure JWT_ALGORITHM is consistent

### "User not found" Error

- Verify user exists in database
- Check if user `is_active=True`

### Middleware Not Working

- Ensure `JWTAuthMiddleware` is added to middleware list
- Check middleware order (should be early in the list)
- Verify database session is available in app state

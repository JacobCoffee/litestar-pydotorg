# Authentication Quick Reference

## Files Created

### Core Auth Module (`src/pydotorg/core/auth/`)
- `password.py` - Password hashing with bcrypt and strength validation
- `jwt.py` - JWT token creation and validation utilities
- `schemas.py` - Pydantic models for auth requests/responses
- `middleware.py` - JWT authentication middleware
- `guards.py` - Route-level authorization guards
- `__init__.py` - Public API exports

### Domain Layer (`src/pydotorg/domains/users/`)
- `auth_controller.py` - Authentication endpoints (login, register, logout, etc.)

### Tests
- `tests/unit/test_auth.py` - Unit tests for password and JWT services
- `tests/integration/test_auth_endpoints.py` - Integration tests for auth endpoints
- `tests/conftest.py` - Updated with db_session fixture

## Configuration in main.py

```python
from litestar.middleware import DefineMiddleware
from pydotorg.core.auth import JWTAuthMiddleware
from pydotorg.domains.users.auth_controller import AuthController

app = Litestar(
    route_handlers=[
        # ... existing handlers
        AuthController,
    ],
    middleware=[
        DefineMiddleware(JWTAuthMiddleware),
    ],
    # ... rest of config
)
```

## Environment Variables

Add to `.env`:
```env
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=10080
```

## API Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/api/auth/register` | No | Register new user |
| POST | `/api/auth/login` | No | Login user |
| POST | `/api/auth/refresh` | No | Refresh access token |
| POST | `/api/auth/logout` | Yes | Logout user |
| POST | `/api/auth/me` | Yes | Get current user info |

## Guards Usage

```python
from pydotorg.core.auth import (
    require_authenticated,
    require_staff,
    require_admin,
    require_membership,
    require_higher_membership,
)

# On controller level
class MyController(Controller):
    guards = [require_authenticated]

# On route level
@get("/admin", guards=[require_admin])
async def admin_only(self) -> dict:
    return {"message": "Admin access"}
```

## Testing

```bash
# Run all auth tests
uv run pytest tests/unit/test_auth.py tests/integration/test_auth_endpoints.py -v

# Run with coverage
uv run pytest tests/unit/test_auth.py --cov=src/pydotorg/core/auth

# Run all checks before commit
make ci
```

## Common Patterns

### Accessing Current User
```python
from pydotorg.domains.users.models import User

@get("/profile", guards=[require_authenticated])
async def profile(self, request: Request) -> dict:
    user: User = request.user
    return {"username": user.username}
```

### Protected Route
```python
@post("/create", guards=[require_authenticated])
async def create(self, data: CreateDTO) -> ResponseDTO:
    # Only authenticated users can access
    pass
```

### Admin Only Route
```python
@delete("/users/{user_id:uuid}", guards=[require_admin])
async def delete_user(self, user_id: UUID) -> None:
    # Only superusers can access
    pass
```

## Security Checklist

- [x] Passwords hashed with bcrypt
- [x] Password strength validation
- [x] JWT token expiration
- [x] Refresh token support
- [x] User inactive check
- [x] Type hints throughout
- [x] Async operations
- [x] Comprehensive tests
- [ ] Rate limiting (TODO)
- [ ] Email verification (TODO)
- [ ] Password reset (TODO)
- [ ] Two-factor auth (TODO)

## Next Steps

1. Copy `.env.example` to `.env` and set `SECRET_KEY`
2. Run database migrations: `uv run alembic upgrade head`
3. Update `main.py` with auth configuration
4. Run tests: `make test`
5. Start server: `make run-dev-server`
6. Test endpoints with curl or Postman

## Example Request Flow

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123"
  }'

# Get current user (use token from login response)
curl -X POST http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

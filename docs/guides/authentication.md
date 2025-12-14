# Authentication Guide

Comprehensive guide to authenticating with the Python.org API.

## Overview

The Python.org API supports two authentication methods:

1. **JWT (JSON Web Tokens)** - Stateless, token-based authentication ideal for API clients
2. **Session-based** - Cookie-based authentication backed by Redis, ideal for web applications

Both methods provide the same level of access and security. Choose based on your use case.

## JWT Authentication (Recommended for APIs)

JWT authentication uses Bearer tokens included in the `Authorization` header.

### Token Types

| Token Type | Purpose | Lifetime |
|-----------|---------|----------|
| Access Token | API access | 7 days |
| Refresh Token | Renew access tokens | 30 days |
| Verification Token | Email verification | 24 hours |
| Password Reset Token | Password reset | 1 hour |

### Register a New User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "pythonista",
    "email": "pythonista@example.com",
    "password": "SecurePass123!",
    "first_name": "Guido",
    "last_name": "van Rossum"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "pythonista", "password": "SecurePass123!"}'
```

### Using JWT Tokens

Include the access token in the `Authorization` header:

```python
import httpx

access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

headers = {
    "Authorization": f"Bearer {access_token}"
}

response = httpx.post(
    "http://localhost:8000/api/auth/me",
    headers=headers
)

print(response.json())
```

### Refreshing Tokens

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your_refresh_token"}'
```

## Session-Based Authentication

Session authentication uses HTTP-only cookies backed by Redis.

### Login with Session

```bash
curl -X POST http://localhost:8000/api/auth/session/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"username": "pythonista", "password": "SecurePass123!"}'
```

### Using Session Cookies

```python
import httpx

client = httpx.Client()

# Login
response = client.post(
    "http://localhost:8000/api/auth/session/login",
    json={"username": "pythonista", "password": "SecurePass123!"}
)

# Make authenticated request (cookies are sent automatically)
response = client.post("http://localhost:8000/api/auth/me")
print(response.json())
```

## OAuth2 Authentication

Authenticate using GitHub or Google OAuth2.

### Supported Providers

| Provider | Scopes |
|----------|--------|
| GitHub | `user:email` |
| Google | `openid email profile` |

### OAuth Flow

1. Redirect user to OAuth provider:

```
GET /api/auth/oauth/github
```

2. User authorizes on provider's site

3. Provider redirects back with authorization code

4. Exchange code for tokens:

```
GET /api/auth/oauth/github/callback?code=...&state=...
```

### Python OAuth Example

```python
import httpx
from urllib.parse import urlparse, parse_qs

def oauth_login(provider: str = "github"):
    client = httpx.Client(follow_redirects=False)

    # Get authorization URL
    response = client.get(
        f"http://localhost:8000/api/auth/oauth/{provider}"
    )

    auth_url = response.headers["location"]
    print(f"Visit this URL to authorize: {auth_url}")

    # After authorization, paste the callback URL
    callback_url = input("Paste the callback URL here: ")

    parsed = urlparse(callback_url)
    params = parse_qs(parsed.query)
    code = params["code"][0]
    state = params["state"][0]

    # Exchange code for tokens
    callback_response = client.get(
        f"http://localhost:8000/api/auth/oauth/{provider}/callback",
        params={"code": code, "state": state}
    )

    tokens = callback_response.json()
    return tokens["access_token"]
```

## Protected Endpoints

### Get Current User

```bash
curl -X POST http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "pythonista",
  "email": "pythonista@example.com",
  "first_name": "Guido",
  "last_name": "van Rossum",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "email_verified": true,
  "has_membership": true
}
```

## Authorization Guards

The API uses role-based guards for access control:

| Guard | Required Permissions |
|-------|---------------------|
| `require_authenticated` | Any authenticated user |
| `require_staff` | `is_staff=True` |
| `require_admin` | `is_superuser=True` |
| `require_membership` | Active PSF membership |

### Permission Errors

```json
// 401 - Not authenticated
{
  "detail": "Authentication required",
  "status_code": 401
}

// 403 - Insufficient permissions
{
  "detail": "Staff privileges required",
  "status_code": 403
}
```

## Email Verification

### Send Verification Email

```bash
curl -X POST http://localhost:8000/api/auth/send-verification \
  -H "Content-Type: application/json" \
  -d '{"email": "pythonista@example.com"}'
```

### Verify Email

```
GET /api/auth/verify-email/{token}
```

## Password Management

### Forgot Password

```bash
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "pythonista@example.com"}'
```

### Reset Password

```bash
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"token": "reset_token", "new_password": "NewSecurePass456!"}'
```

## Token Management Class

```python
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None

    def set_tokens(self, token_response: dict):
        self.access_token = token_response["access_token"]
        self.refresh_token = token_response["refresh_token"]
        self.expires_at = datetime.now() + timedelta(
            seconds=token_response["expires_in"]
        )

    def is_expired(self) -> bool:
        if not self.expires_at:
            return True
        return datetime.now() >= self.expires_at - timedelta(minutes=5)

    def get_access_token(self) -> str:
        if self.is_expired():
            self.refresh()
        return self.access_token

    def refresh(self):
        import httpx
        response = httpx.post(
            "http://localhost:8000/api/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        response.raise_for_status()
        self.set_tokens(response.json())
```

## Best Practices

1. **Never commit tokens** - Store in environment variables or secure vaults
2. **Use HTTPS** - All production traffic must use HTTPS
3. **Rotate tokens** - Refresh access tokens regularly
4. **Validate on client** - Check token expiration before requests
5. **Secure storage** - Use httpOnly cookies for web apps

## Endpoints Reference

| Method | Endpoint | Auth Required | Purpose |
|--------|----------|---------------|---------|
| POST | `/api/auth/register` | No | Create account |
| POST | `/api/auth/login` | No | JWT login |
| POST | `/api/auth/refresh` | No | Refresh JWT |
| POST | `/api/auth/logout` | Yes | Logout (JWT) |
| POST | `/api/auth/session/login` | No | Session login |
| POST | `/api/auth/session/logout` | Yes | Session logout |
| POST | `/api/auth/me` | Yes | Get user info |
| GET | `/api/auth/oauth/{provider}` | No | Start OAuth |
| GET | `/api/auth/oauth/{provider}/callback` | No | OAuth callback |
| POST | `/api/auth/send-verification` | No | Send verification |
| GET | `/api/auth/verify-email/{token}` | No | Verify email |
| POST | `/api/auth/forgot-password` | No | Request reset |
| POST | `/api/auth/reset-password` | No | Reset password |

## See Also

- [API Usage Guide](api-usage.md) - General API usage
- [Rate Limiting](../architecture/RATE_LIMITING_ARCHITECTURE.md) - Rate limiting details

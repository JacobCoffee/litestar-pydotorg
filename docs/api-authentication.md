# API Authentication Guide

Comprehensive guide to authenticating with the Python.org API.

## Overview

The Python.org API supports two authentication methods:

1. **JWT (JSON Web Tokens)** - Stateless, token-based authentication ideal for API clients
2. **Session-based** - Cookie-based authentication backed by Redis, ideal for web applications

Both methods provide the same level of access and security. Choose based on your use case.

## Authentication Methods

### JWT Authentication (Recommended for APIs)

JWT authentication uses Bearer tokens that are included in the `Authorization` header of your requests.

#### Token Types

The system uses three types of JWT tokens:

| Token Type | Purpose | Default Lifetime | Included Claims |
|-----------|---------|------------------|-----------------|
| Access Token | API access | 7 days (10,080 minutes) | `sub` (user_id), `exp`, `iat`, `type: "access"` |
| Refresh Token | Renew access tokens | 30 days | `sub` (user_id), `exp`, `iat`, `type: "refresh"` |
| Verification Token | Email verification | 24 hours | `sub` (user_id), `email`, `exp`, `iat`, `type: "verify_email"` |
| Password Reset Token | Password reset | 1 hour | `sub` (user_id), `email`, `exp`, `iat`, `type: "password_reset"` |

#### Token Format

All tokens are signed using the HS256 algorithm. A typical JWT payload looks like:

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "exp": 1735689600,
  "iat": 1735084800,
  "type": "access"
}
```

**Claims:**
- `sub`: User ID (UUID as string)
- `exp`: Expiration timestamp (Unix epoch)
- `iat`: Issued at timestamp (Unix epoch)
- `type`: Token type (`access`, `refresh`, `verify_email`, or `password_reset`)

#### Register a New User

Create a new account and receive JWT tokens.

**Endpoint:** `POST /api/auth/register`

**Request:**
```json
{
  "username": "pythonista",
  "email": "pythonista@example.com",
  "password": "SecurePass123!",
  "first_name": "Guido",
  "last_name": "van Rossum"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

**Notes:**
- Password must be at least 8 characters
- A verification email is sent automatically
- Tokens are issued immediately (email verification not required to use API)
- `expires_in` is in seconds (604800 = 7 days)

**Error Responses:**

```json
// 403 - Username taken
{
  "detail": "Username already exists",
  "status_code": 403
}

// 403 - Email taken
{
  "detail": "Email already registered",
  "status_code": 403
}

// 403 - Weak password
{
  "detail": "Password does not meet requirements",
  "status_code": 403
}
```

#### Login with Credentials

Authenticate with username and password.

**Endpoint:** `POST /api/auth/login`

**Request:**
```json
{
  "username": "pythonista",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

**Error Responses:**

```json
// 403 - Invalid credentials
{
  "detail": "Invalid credentials",
  "status_code": 403
}

// 403 - OAuth account
{
  "detail": "This account uses github login",
  "status_code": 403
}

// 403 - Inactive account
{
  "detail": "Account is inactive",
  "status_code": 403
}
```

#### Refresh Access Token

Exchange a refresh token for new access and refresh tokens.

**Endpoint:** `POST /api/auth/refresh`

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

**Error Responses:**

```json
// 403 - Invalid token
{
  "detail": "Invalid refresh token",
  "status_code": 403
}

// 403 - User not found/inactive
{
  "detail": "User not found or inactive",
  "status_code": 403
}
```

#### Using JWT Tokens

Include the access token in the `Authorization` header:

**Python Example:**
```python
import httpx

access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

headers = {
    "Authorization": f"Bearer {access_token}"
}

response = httpx.get(
    "https://python.org/api/auth/me",
    headers=headers
)

print(response.json())
```

**cURL Example:**
```bash
curl -X POST https://python.org/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**JavaScript Example:**
```javascript
const accessToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";

const response = await fetch("https://python.org/api/auth/me", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${accessToken}`
  }
});

const userData = await response.json();
console.log(userData);
```

#### Logout (JWT)

Invalidate tokens (client-side action).

**Endpoint:** `POST /api/auth/logout`

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out"
}
```

**Important:** JWT tokens are stateless. The server cannot invalidate them before expiration. Clients should:
1. Delete stored tokens immediately
2. Stop using the tokens in requests
3. Consider implementing a token blacklist if needed

---

### Session-Based Authentication (For Web Apps)

Session authentication uses HTTP-only cookies backed by Redis. Sessions are automatically refreshed on each request.

#### Configuration

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Session Cookie Name | `session_id` | Cookie name for session ID |
| Session Lifetime | 7 days (10,080 minutes) | Automatic expiration time |
| Cookie Security | `httponly=True`, `samesite=lax` | Security flags |
| Cookie Secure Flag | `True` in production, `False` in debug | HTTPS-only in production |

#### Login with Session

Create a session-based login.

**Endpoint:** `POST /api/auth/session/login`

**Request:**
```json
{
  "username": "pythonista",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Successfully logged in"
}
```

**Response Headers:**
```
Set-Cookie: session_id=8yH3kL9mP2vN5qR7wX4jZ6fT1cB0dG3s;
            Max-Age=604800;
            Path=/;
            HttpOnly;
            SameSite=Lax
```

**Python Example (with httpx):**
```python
import httpx

client = httpx.Client()

response = client.post(
    "https://python.org/api/auth/session/login",
    json={
        "username": "pythonista",
        "password": "SecurePass123!"
    }
)

session_cookie = response.cookies.get("session_id")

protected_response = client.post("https://python.org/api/auth/me")
print(protected_response.json())
```

#### Using Session Cookies

Once logged in, the session cookie is automatically sent with subsequent requests.

**Characteristics:**
- Automatically included by browsers
- Refreshed on each request (rolling expiration)
- Stored in Redis with user ID
- Secure and httpOnly flags prevent XSS

#### Logout (Session)

Destroy the session and clear the cookie.

**Endpoint:** `POST /api/auth/session/logout`

**Request:** (Session cookie automatically sent)

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out"
}
```

**Response Headers:**
```
Set-Cookie: session_id=; Path=/; Max-Age=0
```

**Server Actions:**
1. Deletes session from Redis
2. Clears the session cookie
3. User must log in again

---

## OAuth2 Authentication

Authenticate using GitHub or Google OAuth2 providers.

### Supported Providers

| Provider | Scopes | User Data Retrieved |
|----------|--------|---------------------|
| GitHub | `user:email` | Profile, primary email, verification status |
| Google | `openid email profile` | Profile, email, verification status |

### OAuth2 Flow

#### 1. Initiate OAuth Login

Redirect the user to the OAuth provider.

**Endpoint:** `GET /api/auth/oauth/{provider}`

**Providers:** `github` or `google`

**Example:**
```bash
# Redirect user to:
https://python.org/api/auth/oauth/github
```

**Server Actions:**
1. Generates secure state token
2. Stores state in session
3. Redirects to provider's authorization URL

**GitHub Authorization URL:**
```
https://github.com/login/oauth/authorize?
  client_id=your_client_id&
  redirect_uri=https://python.org/api/auth/oauth/github/callback&
  response_type=code&
  scope=user:email&
  state=8yH3kL9mP2vN5qR7wX4jZ6fT1cB0dG3s
```

**Google Authorization URL:**
```
https://accounts.google.com/o/oauth2/v2/auth?
  client_id=your_client_id&
  redirect_uri=https://python.org/api/auth/oauth/google/callback&
  response_type=code&
  scope=openid+email+profile&
  state=8yH3kL9mP2vN5qR7wX4jZ6fT1cB0dG3s
```

#### 2. OAuth Callback

After user authorizes, the provider redirects back with an authorization code.

**Endpoint:** `GET /api/auth/oauth/{provider}/callback?code=...&state=...`

**Query Parameters:**
- `code`: Authorization code from provider
- `state`: State token for CSRF protection

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

**Server Actions:**
1. Validates state token (CSRF protection)
2. Exchanges code for access token
3. Retrieves user profile from provider
4. Creates or updates user account:
   - Existing user: Links OAuth provider to account
   - New user: Creates account with OAuth details
   - Username conflicts: Appends random suffix
5. Marks email as verified (if provider confirms)
6. Returns JWT tokens for API access

**Account Linking Logic:**
- If OAuth email matches existing account without OAuth: Link provider
- If OAuth email matches account with different provider: Error
- If new user: Create account with `oauth_provider` and `oauth_id`
- Password field is `null` for OAuth-only accounts

**Error Responses:**

```json
// 403 - Invalid state (CSRF)
{
  "detail": "Invalid OAuth state",
  "status_code": 403
}

// 403 - Email conflict
{
  "detail": "Email already registered with google",
  "status_code": 403
}

// 403 - Provider mismatch
{
  "detail": "OAuth provider mismatch",
  "status_code": 403
}
```

### Complete OAuth Example (Python)

```python
import httpx
from urllib.parse import urlparse, parse_qs

def oauth_login(provider: str = "github"):
    client = httpx.Client(follow_redirects=False)

    response = client.get(
        f"https://python.org/api/auth/oauth/{provider}"
    )

    auth_url = response.headers["location"]
    print(f"Visit this URL to authorize: {auth_url}")

    callback_url = input("Paste the callback URL here: ")

    parsed = urlparse(callback_url)
    params = parse_qs(parsed.query)
    code = params["code"][0]
    state = params["state"][0]

    callback_response = client.get(
        f"https://python.org/api/auth/oauth/{provider}/callback",
        params={"code": code, "state": state}
    )

    tokens = callback_response.json()
    return tokens["access_token"]
```

---

## Protected Endpoints

### Get Current User

Retrieve authenticated user information.

**Endpoint:** `POST /api/auth/me`

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** `200 OK`
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
  "date_joined": "2025-01-01T00:00:00Z",
  "last_login": "2025-01-15T10:30:00Z",
  "has_membership": true,
  "oauth_provider": null,
  "oauth_id": null
}
```

**Error Response:**

```json
// 401 - Not authenticated
{
  "detail": "Authentication required",
  "status_code": 401
}
```

---

## Authorization Guards

The API uses role-based guards to control access to specific endpoints.

### Access Levels

| Guard | Required Permissions | Use Cases |
|-------|---------------------|-----------|
| `require_authenticated` | Any authenticated user | View profile, submit content |
| `require_staff` | `is_staff=True` | Moderate content, manage users |
| `require_admin` | `is_superuser=True` | Full system access, dangerous operations |
| `require_membership` | Active PSF membership | Member-only features, voting |
| `require_higher_membership` | PSF membership (non-BASIC) | Advanced member features |

### Guard Hierarchy

Guards build on each other:
- `require_staff` includes `require_authenticated`
- `require_admin` includes `require_authenticated`
- `require_higher_membership` includes `require_membership` includes `require_authenticated`

### Permission Errors

**401 Unauthorized:**
```json
{
  "detail": "Authentication required",
  "status_code": 401
}
```

**403 Forbidden (Staff Required):**
```json
{
  "detail": "Staff privileges required",
  "status_code": 403
}
```

**403 Forbidden (Admin Required):**
```json
{
  "detail": "Administrator privileges required",
  "status_code": 403
}
```

**403 Forbidden (Membership Required):**
```json
{
  "detail": "PSF membership required",
  "status_code": 403
}
```

**403 Forbidden (Higher Membership Required):**
```json
{
  "detail": "Higher level PSF membership required",
  "status_code": 403
}
```

### Checking Permissions

Use the `/api/auth/me` endpoint to check your current permissions:

```python
import httpx

response = httpx.post(
    "https://python.org/api/auth/me",
    headers={"Authorization": f"Bearer {access_token}"}
)

user = response.json()

if user["is_staff"]:
    print("You have staff access")
if user["is_superuser"]:
    print("You have admin access")
if user["has_membership"]:
    print("You have PSF membership")
```

---

## Email Verification

Email verification is optional for API usage but recommended for security.

### Send Verification Email

Request a new verification email.

**Endpoint:** `POST /api/auth/send-verification`

**Request:**
```json
{
  "email": "pythonista@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "Verification email sent"
}
```

**Notes:**
- If email is already verified: Returns success message
- If user not found: Returns 404
- Verification link expires in 24 hours

### Verify Email

Verify email address using token from email.

**Endpoint:** `GET /api/auth/verify-email/{token}`

**Example:**
```
GET /api/auth/verify-email/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** `200 OK`
```json
{
  "message": "Email verified successfully"
}
```

**Error Responses:**

```json
// 403 - Invalid/expired token
{
  "detail": "Invalid or expired verification token",
  "status_code": 403
}

// 404 - User not found
{
  "detail": "User not found",
  "status_code": 404
}
```

### Resend Verification (Authenticated)

Resend verification email for current user.

**Endpoint:** `POST /api/auth/resend-verification`

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** `200 OK`
```json
{
  "message": "Verification email sent"
}
```

---

## Password Management

### Forgot Password

Request a password reset link.

**Endpoint:** `POST /api/auth/forgot-password`

**Request:**
```json
{
  "email": "pythonista@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "If an account exists with this email, you will receive a password reset link"
}
```

**Notes:**
- Always returns same message (prevents email enumeration)
- OAuth accounts do not receive reset emails
- Reset link expires in 1 hour

### Reset Password

Set a new password using reset token.

**Endpoint:** `POST /api/auth/reset-password`

**Request:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "NewSecurePass456!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset successfully"
}
```

**Error Responses:**

```json
// 403 - Invalid token
{
  "detail": "Invalid or expired reset token",
  "status_code": 403
}

// 403 - OAuth account
{
  "detail": "This account uses github login. Password cannot be reset.",
  "status_code": 403
}

// 403 - Weak password
{
  "detail": "Password does not meet requirements",
  "status_code": 403
}
```

---

## Error Handling

### Common Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | OK | Successful request |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but lacking permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error in request data |

### Error Response Format

All errors follow this structure:

```json
{
  "detail": "Human-readable error message",
  "status_code": 403,
  "extra": {}
}
```

### Token Expiration

When an access token expires:

```json
{
  "detail": "Invalid token",
  "status_code": 403
}
```

**Solution:** Use your refresh token to get a new access token via `POST /api/auth/refresh`.

### Handling Expired Refresh Tokens

If your refresh token expires, you must log in again:

```python
import httpx

def get_with_auto_refresh(url: str, access_token: str, refresh_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = httpx.get(url, headers=headers)

    if response.status_code == 403:
        refresh_response = httpx.post(
            "https://python.org/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        if refresh_response.status_code == 200:
            new_tokens = refresh_response.json()
            headers["Authorization"] = f"Bearer {new_tokens['access_token']}"
            response = httpx.get(url, headers=headers)
        else:
            raise Exception("Please log in again")

    return response
```

---

## Best Practices

### Security

1. **Never commit tokens** - Store in environment variables or secure vaults
2. **Use HTTPS** - All production traffic must use HTTPS
3. **Rotate tokens** - Refresh access tokens regularly
4. **Validate on client** - Check token expiration before requests
5. **Secure storage** - Use httpOnly cookies for web apps, secure storage for mobile

### Token Management

```python
import os
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None

    def set_tokens(self, token_response):
        self.access_token = token_response["access_token"]
        self.refresh_token = token_response["refresh_token"]
        self.expires_at = datetime.now() + timedelta(
            seconds=token_response["expires_in"]
        )

    def is_expired(self):
        if not self.expires_at:
            return True
        return datetime.now() >= self.expires_at - timedelta(minutes=5)

    def get_access_token(self):
        if self.is_expired():
            self.refresh()
        return self.access_token

    def refresh(self):
        import httpx
        response = httpx.post(
            "https://python.org/api/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        response.raise_for_status()
        self.set_tokens(response.json())
```

### Rate Limiting

Be mindful of rate limits (details vary by endpoint). Best practices:
- Cache responses when possible
- Implement exponential backoff on failures
- Batch requests when available
- Respect `Retry-After` headers

### Testing Authentication

```python
import pytest
import httpx

@pytest.fixture
def authenticated_client():
    client = httpx.Client(base_url="https://python.org")

    response = client.post("/api/auth/login", json={
        "username": "test_user",
        "password": "test_password"
    })

    tokens = response.json()
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"

    yield client

    client.post("/api/auth/logout")


def test_protected_endpoint(authenticated_client):
    response = authenticated_client.post("/api/auth/me")
    assert response.status_code == 200
    assert "username" in response.json()
```

---

## Migration Guide

### From Session to JWT

If you're switching from session-based to JWT authentication:

```python
import httpx

client = httpx.Client()

response = client.post("https://python.org/api/auth/session/login", json={
    "username": "pythonista",
    "password": "SecurePass123!"
})

response = client.post("https://python.org/api/auth/login", json={
    "username": "pythonista",
    "password": "SecurePass123!"
})

tokens = response.json()
access_token = tokens["access_token"]

client.headers["Authorization"] = f"Bearer {access_token}"
```

### From OAuth to Standard Login

OAuth accounts without passwords cannot use standard login. Users must:
1. Continue using OAuth, or
2. Request password reset (which will fail for OAuth accounts)

OAuth accounts are identified by:
- `oauth_provider` is not null (`"github"` or `"google"`)
- `password_hash` is null

---

## Quick Reference

### Endpoints Summary

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
| POST | `/api/auth/resend-verification` | Yes | Resend verification |
| POST | `/api/auth/forgot-password` | No | Request reset |
| POST | `/api/auth/reset-password` | No | Reset password |

### Token Lifetimes Quick Reference

| Token Type | Lifetime | Renewable |
|-----------|----------|-----------|
| Access Token | 7 days | Yes (via refresh) |
| Refresh Token | 30 days | Yes (new token on refresh) |
| Session | 7 days | Yes (auto on each request) |
| Verification Token | 24 hours | Yes (request new) |
| Reset Token | 1 hour | Yes (request new) |

### Headers Quick Reference

```bash
# JWT Authentication
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Session Authentication (automatic via cookie)
Cookie: session_id=8yH3kL9mP2vN5qR7wX4jZ6fT1cB0dG3s
```

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/python/pythondotorg/issues
- Security Issues: security@python.org
- General Questions: https://discuss.python.org/

## See Also

- [API Reference](/docs/api-reference.md)
- [User Management API](/docs/api-users.md)
- [Rate Limiting](/docs/rate-limiting.md)

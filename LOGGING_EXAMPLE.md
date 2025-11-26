# Structured Logging Usage Examples

This document shows how to use the configured structlog logging in your controllers.

## Auth Controller Example

Add these logging statements to `src/pydotorg/domains/users/auth_controller.py`:

### 1. Import the logger at the module level (already added):

```python
from pydotorg.core.logging import bind_user_context, get_logger, unbind_user_context

logger = get_logger(__name__)
```

### 2. Add logging to the register method:

```python
@post("/register")
async def register(
    self,
    data: RegisterRequest,
    db_session: AsyncSession,
) -> TokenResponse:
    logger.info("User registration attempt", username=data.username, email=data.email)

    # ... existing code to check for existing user ...

    if existing_user:
        logger.warning(
            "Registration failed: user already exists",
            username=data.username,
            email=data.email,
            conflict="username" if existing_user.username == data.username else "email",
        )
        # ... raise exception ...

    # ... after user is created and saved ...
    logger.info("User registered successfully", user_id=str(user.id), username=user.username)
    bind_user_context(user.id, user.username)

    # ... create tokens ...

    unbind_user_context()
    return TokenResponse(...)
```

### 3. Add logging to the login method:

```python
@post("/login")
async def login(
    self,
    data: LoginRequest,
    db_session: AsyncSession,
) -> TokenResponse:
    logger.info("User login attempt", username=data.username)

    # ... get user ...

    if not user or not password_service.verify_password(data.password, user.password_hash):
        logger.warning("Login failed: invalid credentials", username=data.username)
        raise PermissionDeniedException("Invalid credentials")

    if not user.is_active:
        logger.warning("Login failed: inactive account", username=data.username, user_id=str(user.id))
        raise PermissionDeniedException("Account is inactive")

    # ... update last_login ...

    logger.info("User logged in successfully", user_id=str(user.id), username=user.username)
    bind_user_context(user.id, user.username)

    # ... create tokens ...

    unbind_user_context()
    return TokenResponse(...)
```

## General Usage Patterns

### Basic Logging

```python
from pydotorg.core.logging import get_logger

logger = get_logger(__name__)

# Info level
logger.info("Operation completed", operation="create_user", duration_ms=45)

# Warning level
logger.warning("Rate limit approaching", user_id=123, requests=95, limit=100)

# Error level with exception
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", operation="risky_operation", error=str(e), exc_info=True)
```

### Using Context Variables

```python
from pydotorg.core.logging import bind_user_context, unbind_user_context, bind_correlation_id

# Bind user context for all subsequent log messages in this async context
bind_user_context(user_id=123, username="john_doe")
logger.info("Processing request")  # Will include user_id and username
unbind_user_context()

# Bind correlation ID for request tracing
bind_correlation_id("req-abc-123")
logger.info("Starting long operation")
# ... do work ...
logger.info("Completed long operation")
```

### Using Request Logger

In route handlers, you can access the request logger:

```python
@get("/api/users/{user_id:int}")
async def get_user(
    self,
    request: Request,
    user_id: int,
) -> UserResponse:
    request.logger.info("Fetching user", user_id=user_id)
    # ... fetch user ...
    return user
```

## Configuration

Logging is configured automatically based on the environment:

- **Development (APP_ENV=dev)**: Console output with colors, DEBUG level
- **Staging (APP_ENV=staging)**: Console output, INFO level
- **Production (APP_ENV=prod)**: JSON output, WARNING level

### Environment Variables

```bash
# Override log level
LOG_LEVEL=DEBUG

# Override log format (console or json)
LOG_FORMAT=json

# Optional: Log to file
LOG_FILE=/var/log/pydotorg/app.log
```

## Log Fields

All logs automatically include:

- `timestamp`: ISO-8601 formatted timestamp
- `logger`: Logger name (module path)
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `event`: Log message

Request/response logs include:

- `method`: HTTP method
- `path`: Request path
- `path_params`: Path parameters
- `query`: Query parameters
- `content_type`: Request content type
- `status_code`: Response status code

Bound context includes:

- `correlation_id`: Request correlation ID (when set)
- `user_id`: Current user ID (when bound)
- `username`: Current username (when bound)

## Example Output

### Development (Console):

```
2025-01-15T14:32:01.123456Z [info     ] User login attempt             username=john_doe
2025-01-15T14:32:01.234567Z [info     ] User logged in successfully    user_id=123 username=john_doe
```

### Production (JSON):

```json
{"timestamp": "2025-01-15T14:32:01.123456Z", "level": "info", "logger": "pydotorg.domains.users.auth_controller", "event": "User login attempt", "username": "john_doe"}
{"timestamp": "2025-01-15T14:32:01.234567Z", "level": "info", "logger": "pydotorg.domains.users.auth_controller", "event": "User logged in successfully", "user_id": "123", "username": "john_doe"}
```

# Structured Logging Implementation

This document describes the structured logging implementation using `structlog` in the litestar-pydotorg project.

## Overview

Structured logging has been implemented using Litestar's built-in structlog integration. The implementation provides:

- Environment-based configuration (dev/staging/prod)
- Console output for development with colors
- JSON output for production for machine-parseable logs
- Request/response logging middleware
- Correlation ID support
- User context binding
- Clean logger factory for use across the application

## Files Created/Modified

### Created Files

1. **`src/pydotorg/core/logging.py`** - Core logging configuration module
   - `configure_structlog()`: Main configuration function
   - `get_logger()`: Logger factory
   - `bind_correlation_id()` / `unbind_correlation_id()`: Correlation ID helpers
   - `bind_user_context()` / `unbind_user_context()`: User context helpers

2. **`LOGGING_EXAMPLE.md`** - Usage examples and patterns

### Modified Files

1. **`src/pydotorg/config.py`** - Added logging configuration fields:
   - `log_format`: Logging format ('console' or 'json')
   - `log_file`: Optional log file path
   - `use_json_logging`: Computed property based on environment/format

2. **`src/pydotorg/main.py`** - Integrated structlog plugin:
   - Imported `configure_structlog` and `StructlogPlugin`
   - Created structlog configuration instance
   - Added structlog_plugin to app plugins list

3. **`src/pydotorg/domains/users/auth_controller.py`** - Added logging imports:
   - Imported logger utilities
   - Created module-level logger instance

## Configuration

### Environment-Based Defaults

The logging configuration automatically adjusts based on the `APP_ENV` environment variable:

| Environment | Log Level | Format | Use JSON |
|------------|-----------|---------|----------|
| dev | DEBUG | console | No |
| staging | INFO | console | No |
| prod | WARNING | json | Yes |

### Environment Variables

You can override defaults using these environment variables:

```bash
# Set environment (affects defaults)
APP_ENV=dev|staging|prod

# Override log level
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL

# Override log format
LOG_FORMAT=console|json

# Optional: Log to file (not yet implemented)
LOG_FILE=/var/log/pydotorg/app.log
```

### Configuration Properties

In `settings` (from `pydotorg.config`):

- `settings.log_level`: Current log level (string)
- `settings.log_format`: Current log format ('console' or 'json')
- `settings.use_json_logging`: Boolean indicating JSON vs console
- `settings.log_file`: Optional Path to log file

## Processors

The following structlog processors are configured (in order):

1. `merge_contextvars` - Merge context variables (correlation_id, user_id, etc.)
2. `filter_by_level` - Filter by log level
3. `add_logger_name` - Add logger name to output
4. `add_log_level` - Add log level to output
5. `PositionalArgumentsFormatter` - Format positional arguments
6. `TimeStamper` - Add ISO-8601 timestamp
7. `StackInfoRenderer` - Render stack info when requested
8. `format_exc_info` - Format exception information
9. `UnicodeDecoder` - Decode unicode
10. `JSONRenderer` or `ConsoleRenderer` - Final output formatting

## Middleware Configuration

Request logging middleware captures:

**Request Fields:**
- `method` - HTTP method (GET, POST, etc.)
- `path` - Request path
- `path_params` - Path parameters
- `query` - Query string parameters
- `content_type` - Request content type

**Response Fields:**
- `status_code` - HTTP status code
- `content_type` - Response content type

## Usage Examples

### Basic Logging

```python
from pydotorg.core.logging import get_logger

logger = get_logger(__name__)

# Structured logging with context
logger.info("User action", user_id=123, action="login", ip="192.168.1.1")
logger.warning("Rate limit approaching", user_id=123, count=95, limit=100)
logger.error("Database error", error=str(e), query="SELECT * FROM users", exc_info=True)
```

### Using Request Logger

```python
@get("/api/users/{user_id:int}")
async def get_user(request: Request, user_id: int) -> UserResponse:
    request.logger.info("Fetching user", user_id=user_id)
    # ... implementation ...
    return user
```

### Binding Context

```python
from pydotorg.core.logging import bind_user_context, unbind_user_context, get_logger

logger = get_logger(__name__)

async def handle_authenticated_request(user: User):
    bind_user_context(user.id, user.username)
    try:
        logger.info("Processing request")  # Includes user_id and username
        # ... do work ...
    finally:
        unbind_user_context()
```

### Correlation IDs

```python
from pydotorg.core.logging import bind_correlation_id, get_logger
import uuid

logger = get_logger(__name__)

correlation_id = str(uuid.uuid4())
bind_correlation_id(correlation_id)

logger.info("Starting operation")  # Includes correlation_id
# ... do async work ...
logger.info("Operation complete")  # Same correlation_id
```

## Output Formats

### Development (Console)

```
2025-01-15T14:32:01.123456Z [info     ] User login attempt             username=john_doe
2025-01-15T14:32:01.234567Z [info     ] User logged in successfully    user_id=123 username=john_doe
2025-01-15T14:32:01.345678Z [info     ] GET /api/users/123             method=GET path=/api/users/123 status_code=200
```

### Production (JSON)

```json
{"timestamp":"2025-01-15T14:32:01.123456Z","level":"info","logger":"pydotorg.domains.users.auth_controller","event":"User login attempt","username":"john_doe"}
{"timestamp":"2025-01-15T14:32:01.234567Z","level":"info","logger":"pydotorg.domains.users.auth_controller","event":"User logged in successfully","user_id":"123","username":"john_doe"}
{"timestamp":"2025-01-15T14:32:01.345678Z","level":"info","logger":"litestar","event":"HTTP Request","method":"GET","path":"/api/users/123","status_code":200}
```

## Integration with auth_controller.py

The authentication controller has been prepared for logging. To complete the integration:

1. The logger is already imported at the module level
2. Add logging statements to methods following the examples in `LOGGING_EXAMPLE.md`

Example additions:

```python
# In register method
logger.info("User registration attempt", username=data.username, email=data.email)
# ... after successful registration ...
logger.info("User registered successfully", user_id=str(user.id), username=user.username)

# In login method
logger.info("User login attempt", username=data.username)
# ... after successful login ...
logger.info("User logged in successfully", user_id=str(user.id), username=user.username)
bind_user_context(user.id, user.username)
```

## Best Practices

1. **Use structured fields**: Always pass context as keyword arguments rather than formatting into the message string

   ```python
   # Good
   logger.info("User action", user_id=123, action="login")

   # Bad
   logger.info(f"User {user_id} performed {action}")
   ```

2. **Include relevant context**: Add fields that help with debugging and monitoring

   ```python
   logger.error("API call failed",
                endpoint="/api/users",
                status_code=500,
                duration_ms=1234,
                error=str(e))
   ```

3. **Use appropriate log levels**:
   - `DEBUG`: Detailed diagnostic information
   - `INFO`: Significant business events
   - `WARNING`: Unusual situations that don't prevent operation
   - `ERROR`: Errors that need attention
   - `CRITICAL`: System-level failures

4. **Bind context for scope**: Use context binding for async operations

   ```python
   bind_user_context(user.id, user.username)
   try:
       # All logs in this scope include user context
       await perform_user_operations()
   finally:
       unbind_user_context()
   ```

5. **Log exceptions properly**: Include `exc_info=True` for exception tracebacks

   ```python
   try:
       risky_operation()
   except Exception as e:
       logger.error("Operation failed", operation="risky", error=str(e), exc_info=True)
   ```

## Testing

To verify the logging configuration:

```bash
# Test imports
uv run python -c "from pydotorg.core.logging import get_logger, configure_structlog; print('✓ OK')"

# Test configuration
uv run python -c "from pydotorg.core.logging import configure_structlog; config = configure_structlog(); print('✓ OK')"

# Test settings
uv run python -c "from pydotorg.config import settings; print(f'Level: {settings.log_level}, JSON: {settings.use_json_logging}')"
```

## Future Enhancements

Potential improvements to consider:

1. **File logging**: Implement actual file output when `log_file` is configured
2. **Log rotation**: Add log rotation for file-based logging
3. **Async logging**: Consider async logging for high-throughput scenarios
4. **Custom processors**: Add application-specific processors (e.g., PII redaction)
5. **Metrics integration**: Connect logging events to metrics/monitoring systems
6. **Distributed tracing**: Add OpenTelemetry integration for distributed tracing

## References

- [Structlog Documentation](https://www.structlog.org/)
- [Litestar Logging Documentation](https://docs.litestar.dev/2/usage/logging.html)
- [Litestar Structlog Plugin Reference](https://docs.litestar.dev/2/reference/plugins/structlog.html)
- `LOGGING_EXAMPLE.md` - Practical usage examples

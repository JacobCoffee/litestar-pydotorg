# Feature Flags System

A simple, configuration-based feature flags system for conditionally enabling/disabling functionality in the application.

## Overview

The feature flags system allows you to:

- Enable/disable features via environment variables or configuration
- Protect routes with feature flag guards
- Access feature flags in templates for conditional rendering
- Programmatically check feature status in your code
- Enable maintenance mode across the entire application

## Configuration

Feature flags are configured in `src/pydotorg/config.py` using a nested Pydantic model:

```python
class FeatureFlagsConfig(BaseModel):
    """Feature flags configuration for conditional functionality."""

    enable_oauth: bool = True
    enable_jobs: bool = True
    enable_sponsors: bool = True
    enable_search: bool = True
    maintenance_mode: bool = False
```

### Environment Variables

Override feature flags using environment variables with the `FEATURES__` prefix:

```bash
# Disable OAuth
export FEATURES__ENABLE_OAUTH=false

# Enable maintenance mode
export FEATURES__MAINTENANCE_MODE=true

# Disable jobs
export FEATURES__ENABLE_JOBS=false
```

Or in your `.env` file:

```env
FEATURES__ENABLE_OAUTH=false
FEATURES__MAINTENANCE_MODE=true
```

## Usage

### 1. Route Guards

Protect routes so they're only accessible when a feature is enabled:

```python
from litestar import Controller, get
from pydotorg.core.features import require_feature

class OAuthController(Controller):
    path = "/oauth"

    @get("/login", guards=[require_feature("enable_oauth")])
    async def login(self) -> dict:
        """Only accessible when OAuth is enabled."""
        return {"message": "OAuth login"}
```

When a feature is disabled or maintenance mode is active, the guard will return a `503 Service Unavailable` response.

### 2. Dependency Injection

Inject feature flags into your handlers for programmatic checks:

```python
from litestar import get
from pydotorg.core.features import FeatureFlags

@get("/status")
async def status(feature_flags: FeatureFlags) -> dict:
    """Check feature availability programmatically."""
    response = {"available_features": []}

    if feature_flags.is_enabled("enable_jobs"):
        response["available_features"].append("jobs")

    if feature_flags.is_enabled("enable_sponsors"):
        response["available_features"].append("sponsors")

    return response
```

### 3. Template Usage

Feature flags are automatically available in all Jinja templates via the global context:

```jinja
{# Show OAuth login only when enabled #}
{% if feature_flags.enable_oauth %}
<div class="oauth-section">
    <a href="/oauth/github">Login with GitHub</a>
    <a href="/oauth/google">Login with Google</a>
</div>
{% endif %}

{# Show maintenance banner #}
{% if feature_flags.maintenance_mode %}
<div class="alert alert-warning">
    <strong>Maintenance Mode:</strong> Some features are temporarily unavailable.
</div>
{% endif %}

{# Conditionally show jobs section #}
{% if feature_flags.enable_jobs %}
<div class="jobs-section">
    <a href="/jobs">Browse Job Listings</a>
</div>
{% endif %}
```

### 4. Application State

Feature flags are also available on the application state:

```python
from litestar import Request

@get("/check")
async def check(request: Request) -> dict:
    """Access feature flags from app state."""
    flags = request.app.state.feature_flags
    return {"maintenance_mode": flags.maintenance_mode}
```

## Available Feature Flags

| Flag | Description | Default |
|------|-------------|---------|
| `enable_oauth` | OAuth authentication (GitHub, Google) | `True` |
| `enable_jobs` | Job listings functionality | `True` |
| `enable_sponsors` | Sponsorship management and display | `True` |
| `enable_search` | Site-wide search functionality | `True` |
| `maintenance_mode` | Application-wide maintenance mode | `False` |

## Maintenance Mode

When `maintenance_mode` is enabled:

- All feature flag guards will block access with 503 responses
- Templates can display maintenance banners
- Critical endpoints (health checks, admin) remain accessible

```bash
# Enable maintenance mode
export FEATURES__MAINTENANCE_MODE=true
```

## Architecture

### Core Components

1. **`src/pydotorg/core/features.py`**
   - `FeatureFlags` class: Manages feature flag state
   - `require_feature()` guard factory: Creates route guards

2. **`src/pydotorg/core/dependencies.py`**
   - `provide_feature_flags()`: Dependency provider
   - `get_core_dependencies()`: Aggregates core dependencies

3. **`src/pydotorg/config.py`**
   - `FeatureFlagsConfig`: Pydantic model for configuration
   - Integrated into main `Settings` class

4. **`src/pydotorg/main.py`**
   - Template context processor: Adds flags to templates
   - App initialization: Adds flags to app state

### Data Flow

```
Environment Variables / .env
    ↓
Settings (Pydantic validation)
    ↓
FeatureFlags instance
    ↓
    ├─→ Route Guards (require_feature)
    ├─→ Dependency Injection (handlers)
    ├─→ Template Context (Jinja)
    └─→ App State (request.app.state)
```

## Testing

Feature flags can be easily mocked in tests:

```python
from litestar import Litestar, get
from litestar.testing import TestClient
from pydotorg.core.features import FeatureFlags, require_feature

def test_disabled_feature():
    @get("/test", guards=[require_feature("enable_oauth")])
    def handler() -> dict:
        return {"status": "ok"}

    def init_app(app: Litestar) -> None:
        app.state.feature_flags = FeatureFlags(enable_oauth=False)

    app = Litestar(
        route_handlers=[handler],
        on_app_init=[init_app],
    )

    client = TestClient(app=app)
    response = client.get("/test")
    assert response.status_code == 503
```

## Adding New Feature Flags

To add a new feature flag:

1. Add the field to `FeatureFlagsConfig` in `config.py`:
   ```python
   class FeatureFlagsConfig(BaseModel):
       enable_oauth: bool = True
       enable_new_feature: bool = False  # Add this
   ```

2. Update `FeatureFlags.__init__()` in `features.py`:
   ```python
   def __init__(
       self,
       *,
       enable_oauth: bool = True,
       enable_new_feature: bool = False,  # Add this
   ) -> None:
       self.enable_oauth = enable_oauth
       self.enable_new_feature = enable_new_feature  # Add this
   ```

3. Update `FeatureFlags.to_dict()` in `features.py`:
   ```python
   def to_dict(self) -> dict[str, bool]:
       return {
           "enable_oauth": self.enable_oauth,
           "enable_new_feature": self.enable_new_feature,  # Add this
       }
   ```

4. Update the providers in `dependencies.py` and `main.py` to pass the new flag.

5. Use the feature flag in your code:
   ```python
   @get("/new-feature", guards=[require_feature("enable_new_feature")])
   async def new_feature_endpoint() -> dict:
       return {"message": "New feature"}
   ```

## Best Practices

1. **Use guards for route protection**: Always use `require_feature()` guards rather than manual checks in handlers
2. **Keep flags boolean**: Feature flags should be simple on/off switches
3. **Document flag purpose**: Add clear docstrings explaining what each flag controls
4. **Default to enabled**: New features should default to `True` unless explicitly risky
5. **Clean up old flags**: Remove feature flags once features are stable and permanently enabled
6. **Test both states**: Always test your code with flags both enabled and disabled

## Examples

See the following files for complete examples:

- `docs/feature_flags_example.py` - Controller examples
- `docs/feature_flags_template_example.html` - Template examples
- `tests/core/test_features.py` - Test examples

## Migration Guide

If you're migrating existing code to use feature flags:

### Before
```python
@get("/oauth/login")
async def oauth_login() -> dict:
    if not settings.oauth_enabled:
        raise ServiceUnavailableException("OAuth disabled")
    return {"message": "OAuth login"}
```

### After
```python
@get("/oauth/login", guards=[require_feature("enable_oauth")])
async def oauth_login() -> dict:
    return {"message": "OAuth login"}
```

The guard handles the feature check automatically and provides consistent error responses.

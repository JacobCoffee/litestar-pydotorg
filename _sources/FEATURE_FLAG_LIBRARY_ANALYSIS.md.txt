# Feature Flag Library for Litestar: Analysis & Recommendation

> **Investigation Summary**: Should we create a standalone feature flag library for Litestar?

## Executive Summary

**Recommendation: DO NOT BUILD A SEPARATE LIBRARY**

After comprehensive analysis of the current implementation, Python ecosystem, and community needs, we recommend keeping feature flags as an in-project pattern rather than extracting to a library.

---

## Current Implementation

The `litestar-pydotorg` project contains a well-designed feature flag system in ~107 lines of code:

### Files

| File | Purpose |
|------|---------|
| `src/pydotorg/core/features.py` | Core `FeatureFlags` class + `require_feature()` guard |
| `src/pydotorg/config.py` | Pydantic `FeatureFlagsConfig` integration |
| `src/pydotorg/core/dependencies.py` | Dependency injection provider |
| `src/pydotorg/main.py` | Template context + app state integration |
| `tests/core/test_features.py` | Comprehensive test coverage |
| `docs/FEATURE_FLAGS.md` | Usage documentation |

### Features

- **5 boolean flags**: `enable_oauth`, `enable_jobs`, `enable_sponsors`, `enable_search`, `maintenance_mode`
- **Litestar-native guards**: `require_feature("flag_name")` factory
- **Pydantic configuration**: Environment variable driven (`FEATURES__FLAG_NAME`)
- **Template integration**: Flags available in Jinja2 context
- **Dependency injection**: `FeatureFlags` injectable into handlers
- **App state**: Accessible via `request.app.state.feature_flags`

### Code Example

```python
from litestar import get
from pydotorg.core.features import require_feature, FeatureFlags

@get("/oauth/login", guards=[require_feature("enable_oauth")])
async def oauth_login(feature_flags: FeatureFlags) -> dict:
    # Guard ensures this only executes if enable_oauth is True
    return {"status": "oauth_enabled"}
```

---

## Python Feature Flag Ecosystem

### Existing Solutions

| Library | Type | Litestar Support | Notes |
|---------|------|------------------|-------|
| **LaunchDarkly** | Enterprise SaaS | None | $$$, overkill for simple needs |
| **Unleash** | Open Source + SaaS | None | Requires server infrastructure |
| **Flagsmith** | Open Source + SaaS | None | Self-hostable, but complex |
| **GrowthBook** | Data Warehouse Native | None | Analytics-focused |
| **Django-Waffle** | Django-specific | N/A | Django ORM coupled |
| **fastapi-featureflags** | FastAPI-specific | N/A | ~85 stars, basic features |
| **flipper-client** | Generic Python | None | Lightweight, no framework integration |

### Key Finding

**No existing library has Litestar-specific integrations** (guards, DI, middleware).

However, this gap doesn't justify a new library because:
1. The current in-project implementation fills this need adequately
2. Advanced use cases should use purpose-built services
3. Simple use cases can copy the existing pattern

---

## Build vs. Keep Analysis

### Option 1: Build a Library

| Factor | Assessment |
|--------|------------|
| Development effort | 40-80 hours initial |
| Ongoing maintenance | 5-10 hours/month |
| Adoption likelihood | Low (~85 stars based on fastapi-featureflags) |
| Abandonment risk | High |
| Value added | Saves ~50-100 LOC per project |

**Verdict**: High effort, low reward.

### Option 2: Keep Current Implementation

| Factor | Assessment |
|--------|------------|
| Fits pythondotorg needs | 100% |
| Code volume | ~107 LOC |
| External dependencies | Zero |
| Maintenance burden | None (in-project) |
| Flexibility | Full control |

**Verdict**: Already optimal.

---

## Framework Comparison

| Framework | Built-in Feature Flags? | Ecosystem Approach |
|-----------|------------------------|-------------------|
| Django | No | Third-party (django-waffle) |
| FastAPI | No | Generic Python libs or custom |
| Flask | No | Generic Python libs or custom |
| Rails | No | Third-party (flipper gem) |
| **Litestar** | No | **Should follow same pattern** |

Feature flags are **application infrastructure**, not **framework infrastructure**.

---

## Recommendation

### Primary: Keep In-Project Implementation

The current code is:
- Appropriately simple for the use case
- Well-documented and tested
- Zero external dependencies
- Litestar-native patterns

### Secondary: Document the Pattern

Instead of a library, contribute to Litestar documentation:

1. **Add to Litestar Docs** - "Feature Flags" recipe/how-to guide
2. **Create Template** - Include in `litestar-fullstack` or similar starters
3. **Publish Gist** - Standalone copy-paste module

### What NOT to Do

- Do NOT extract to a separate `litestar-flags` package
- Do NOT add advanced features (percentage rollouts, A/B testing, user segmentation)
- Do NOT integrate with external services for simple boolean flags

---

## When TO Consider a Library

A library might be warranted if:

1. **Multiple Litestar projects** in an organization need shared feature flags
2. **Community demand** emerges (GitHub issues, Discord requests)
3. **Advanced features** become common requirements:
   - Percentage-based rollouts
   - User/group targeting
   - A/B testing
   - Dynamic runtime updates
   - Admin UI

Until then, the pattern approach is sufficient.

---

## Proposed Documentation Structure

If contributing to Litestar docs, suggested structure:

```
docs/
  usage/
    recipes/
      feature-flags.rst
        - Overview
        - Basic Implementation
        - Configuration with Pydantic
        - Route Guards
        - Template Integration
        - Testing Patterns
        - When to Use External Services
```

### Sample Documentation Content

```python
# Feature Flags with Litestar

"""Simple feature flag implementation using Litestar guards."""

from dataclasses import dataclass
from typing import Any
from litestar.connection import ASGIConnection
from litestar.exceptions import HTTPException
from litestar.handlers import BaseRouteHandler

@dataclass
class FeatureFlags:
    enable_feature_a: bool = True
    enable_feature_b: bool = False
    maintenance_mode: bool = False

    def is_enabled(self, feature: str) -> bool:
        if self.maintenance_mode:
            return False
        return getattr(self, feature)

def require_feature(feature: str):
    """Guard factory for feature flag protection."""
    async def guard(
        connection: ASGIConnection,
        _: BaseRouteHandler,
    ) -> None:
        flags = connection.app.state.feature_flags
        if not flags.is_enabled(feature):
            raise HTTPException(status_code=503, detail="Feature unavailable")
    return guard
```

---

## Conclusion

The current feature flag implementation in `litestar-pydotorg` represents a **well-designed, appropriately-scoped solution** that should serve as a **documented pattern** rather than a standalone library.

**Key Reasons**:
- ~107 LOC solves the problem completely
- Zero external dependencies
- Litestar-native patterns (guards, DI, templates)
- Low community demand for a library
- High maintenance burden for marginal value

**Action Items**:
1. Keep current implementation in pythondotorg
2. Propose documentation PR to Litestar
3. Consider template inclusion in litestar-fullstack

---

*Analysis conducted via hive mind investigation with specialized agents: Researcher, Analyst, Architect, Reviewer*

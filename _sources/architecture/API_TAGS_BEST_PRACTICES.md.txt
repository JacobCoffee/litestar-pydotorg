:orphan:

# API Tags - Best Practices & Guidelines

Guidelines for maintaining and extending the API tag structure in the Python.org API.

## Overview

This document provides best practices for working with API tags in the OpenAPI documentation to ensure consistency, maintainability, and optimal developer experience.

## Naming Conventions

### 1. Use Title Case with Spaces

Tags should use Title Case with spaces, NOT kebab-case or camelCase.

```python
# Good
tags = ["User Memberships"]
tags = ["Event Locations"]
tags = ["Admin Email Templates"]

# Bad
tags = ["user-memberships"]
tags = ["userMemberships"]
tags = ["user_memberships"]
```

**Rationale**: Title Case with spaces is much more readable in Scalar UI navigation and creates a more professional appearance.

### 2. Keep Tag Names Concise

Tag names should be descriptive but brief (2-4 words maximum).

```python
# Good
tags = ["Job Review Comments"]   # 3 words, clear
tags = ["Success Stories"]        # 2 words, concise

# Bad
tags = ["User Job Review Comments"]  # Too long, ambiguous
tags = ["Community Contributed Content Posts"]  # Too long
```

### 3. Use Singular or Plural Consistently

Use plural forms for collection resources, singular for singular resources.

```python
# Good
tags = ["Jobs"]                   # Collection
tags = ["Sponsors"]               # Collection
tags = ["Event Occurrences"]      # Collection

# Avoid mixing
tags = ["Job"]                    # Too singular for collection endpoints
tags = ["Event Occurrence"]       # Use plural for consistency
```

### 4. Admin Tag Prefix

All administrative endpoints must use the "Admin " prefix (note the space).

```python
# Good
tags = ["Admin Dashboard"]
tags = ["Admin Email Templates"]
tags = ["Admin Tasks"]

# Bad
tags = ["AdminDashboard"]         # No space
tags = ["Admin-Users"]            # Hyphen, not space
tags = ["administration-users"]   # No prefix
```

### 5. Group Related Concepts

Related tags should use consistent prefixes to show relationships.

```python
# Good - Clear relationships
tags = ["Event Categories"]       # Grouped under "Event"
tags = ["Event Locations"]        # Grouped under "Event"
tags = ["Event Occurrences"]      # Grouped under "Event"

# Less clear
tags = ["Categories"]             # Ambiguous
tags = ["Locations"]              # Ambiguous
tags = ["Occurrences"]            # Ambiguous
```

### 6. Use Specific Resource Terms

Be specific about what resource the tag represents.

```python
# Good
tags = ["User Memberships"]       # Specific: memberships belong to users
tags = ["Blog Feeds"]             # Specific: feeds related to blogs
tags = ["Community Content"]      # Specific: community-contributed content

# Vague
tags = ["Memberships"]            # What kind of memberships?
tags = ["Feeds"]                  # Feeds of what?
tags = ["Content"]                # What type of content?
```

## Controller Organization

### 1. One Tag Per Controller

Each controller class should have exactly one tag (rare exceptions may have two related tags).

```python
# Good
class UserController(Controller):
    tags = ["Users"]

class MembershipController(Controller):
    tags = ["User Memberships"]

# Bad - Multiple unrelated tags
class MixedController(Controller):
    tags = ["Users", "Jobs", "Events"]  # Don't do this
```

### 2. Tag at Class Level, Not Method Level

Define tags at the controller class level, not on individual route methods.

```python
# Good - Tag defined at class level
class JobController(Controller):
    tags = ["Jobs"]

    @get("/")
    async def list_jobs(self) -> list[JobRead]:
        """List all jobs."""
        pass

# Avoid - Tags on individual methods
class JobController(Controller):
    @get("/", tags=["Jobs"])  # Don't do this
    async def list_jobs(self) -> list[JobRead]:
        pass
```

**Rationale**: Tags in OpenAPI are typically defined at operation (route) level, but Litestar controller tags apply to all routes in the controller. Keep it consistent at the class level for simplicity.

### 3. Related Resources Should Be Nearby

If Tag A is about a sub-resource of Tag B, they should be close in the OpenAPI tags list.

```python
# Good ordering - Resource hierarchy
1. Events
2. Event Calendars
3. Event Categories
4. Event Locations
5. Event Occurrences

# Bad ordering - Scattered
1. Events
2. Admin Dashboard
3. Event Calendars
4. Jobs
5. Event Occurrences
```

### 4. Render Controllers Use "internal" Tag

Controllers that serve HTML should use the "internal" tag to exclude them from public API documentation.

```python
# Good - HTML render controllers excluded
class PageRenderController(Controller):
    tags = ["internal"]
    include_in_schema = False  # Explicitly exclude from OpenAPI

    @get("/{slug:str}")
    async def render_page(self, slug: str) -> Template:
        """Render a page as HTML (not in API docs)."""
        pass

# Bad - Render controller in public API
class PageRenderController(Controller):
    tags = ["Pages"]  # Wrong! Pages tag is for API resources
```

**Important**: Controllers that serve HTML templates (not JSON/structured data) should NEVER use public API tags. Always use "internal" or exclude from schema.

## Maintaining the Tag Structure

### 1. When to Add New Tags

Add a new tag when:
- You're adding a major new feature/domain
- The new resource doesn't fit logically into existing tags
- You need to create a new top-level category

**Don't** add new tags for:
- Variations of existing resources (use existing tag)
- Helper controllers (mark as "internal")
- Render controllers (mark as "internal")

```python
# Good - Reuse existing tag for variants
class BlogEntryController(Controller):
    tags = ["Blogs"]  # Both entries and feeds use blog-related tags

class BlogFeedController(Controller):
    tags = ["Blog Feeds"]  # Related to blogs

# Bad - Creating unnecessary tags
class BlogEntryDetailController(Controller):
    tags = ["Blog Entry Details"]  # Too specific

class BlogEntryCommentController(Controller):
    tags = ["Blog Entry Comments"]  # Should group under "Blogs"
```

### 2. Refactoring Tags

When refactoring tags:
1. Update all affected controllers at once
2. Update OpenAPI tag configuration
3. Update documentation (`API_TAGS_QUICK_REF.md`, `API_TAGS_STRUCTURE.md`)
4. Update any integration tests
5. Test in Scalar UI to verify grouping

```python
# When refactoring "community-posts" tag:

# 1. Update controller
class CommunityPostController(Controller):
    tags = ["Community Content"]  # Was: "community-posts"

# 2. Update OpenAPI config
OPENAPI_TAGS = [
    # ... remove old tag ...
    Tag(name="Community Content", description="..."),
]

# 3. Update tests
def test_community_content_tag():
    assert community_post_controller.tags == ["Community Content"]

# 4. Test in Scalar
# Visit http://localhost:8000/docs and verify
```

### 3. Tag Migration Checklist

When migrating or adding tags:

```markdown
- [ ] Identify all affected controllers
- [ ] Update controller tag assignments
- [ ] Update OpenAPI tag configuration
- [ ] Update API_TAGS_QUICK_REF.md
- [ ] Update API_TAGS_STRUCTURE.md (if needed)
- [ ] Update API_TAGS_HIERARCHY.txt (if adding new category)
- [ ] Run tests: `make test`
- [ ] Verify in Scalar UI: `make serve` then visit docs
- [ ] Update any external documentation
- [ ] Create atomic git commit with all changes
```

## OpenAPI Tag Configuration

### 1. Keep Descriptions Clear and Concise

Each tag needs a clear description that helps developers understand what endpoints are in this group.

```python
# Good - Clear and helpful
Tag(
    name="Event Locations",
    description="Physical venues and event locations",
),

# Bad - Vague
Tag(
    name="Event Locations",
    description="Location stuff",  # Too vague
),

# Bad - Too long
Tag(
    name="Event Locations",
    description="This tag contains all endpoints related to managing the physical venues and locations where events can be held, including information about addresses, accessibility, parking, and other venue-related details that help organize Python events",  # Way too long
),
```

### 2. Add External Documentation Links When Applicable

If there's external documentation for a resource category, include a link:

```python
from litestar.openapi.spec import Tag, ExternalDocumentation

Tag(
    name="Python Releases",
    description="Python version releases and release information",
    external_docs=ExternalDocumentation(
        url="https://www.python.org/downloads/release/",
        description="View all Python releases",
    ),
),
```

### 3. Keep Tag Descriptions in English

All tag descriptions should be in clear, professional English suitable for an international developer audience.

```python
# Good
description="User account management, profiles, and account operations"

# Avoid
description="Administrer les comptes utilisateurs et les profils"  # French
description="ユーザーアカウント管理"  # Japanese
```

## Testing Tags

### 1. Test That Tags Are Present

Ensure your controllers have the correct tags:

```python
# tests/integration/test_openapi_tags.py

import pytest
from pydotorg.domains.users.controllers import UserController, MembershipController

class TestOpenAPITags:
    def test_user_controller_has_users_tag(self):
        assert UserController.tags == ["Users"]

    def test_membership_controller_has_user_memberships_tag(self):
        assert MembershipController.tags == ["User Memberships"]

    def test_admin_tags_have_prefix(self):
        from pydotorg.domains.admin.controllers.users import AdminUserController
        assert AdminUserController.tags[0].startswith("Admin ")
```

### 2. Test OpenAPI Schema

Verify tags appear correctly in the generated OpenAPI schema:

```python
def test_openapi_schema_includes_tags(client):
    response = client.get("/api/v1/openapi.json")
    schema = response.json()

    # Check tags are defined
    tag_names = [tag["name"] for tag in schema.get("tags", [])]
    assert "Users" in tag_names
    assert "Jobs" in tag_names
    assert "Admin Dashboard" in tag_names

    # Check no render tags in public schema
    assert "internal" not in tag_names
    assert "jobs-render" not in tag_names
```

### 3. Test Tag Count and Organization

Validate that tags match the documented structure:

```python
def test_openapi_tags_match_documentation(client):
    response = client.get("/api/v1/openapi.json")
    schema = response.json()

    tags = [tag["name"] for tag in schema.get("tags", [])]

    # Should have approximately 50 public tags
    assert len(tags) >= 45  # Allow some flexibility
    assert len(tags) <= 55

    # Admin tags should be grouped
    admin_tags = [t for t in tags if t.startswith("Admin ")]
    assert len(admin_tags) >= 10  # At least 10 admin categories
```

## Documentation

### 1. Update Quick Reference When Adding Tags

Whenever you add a new tag, update `API_TAGS_QUICK_REF.md`:

```markdown
| 51 | New Feature | `new/controllers.py` | Description |
```

### 2. Keep Hierarchy Diagram Current

If adding a major new category, update `API_TAGS_HIERARCHY.txt` to reflect the new grouping.

### 3. Document the Rationale

In `API_TAGS_STRUCTURE.md`, explain why the tag structure is organized the way it is and how it benefits developers.

## Common Patterns

### Pattern 1: Resource with Sub-Resources

When a resource has sub-resources (e.g., Events → Calendars → Categories):

```python
# Main resource
class EventController(Controller):
    tags = ["Events"]

# Sub-resources
class CalendarController(Controller):
    tags = ["Event Calendars"]  # Prefix with parent resource

class EventCategoryController(Controller):
    tags = ["Event Categories"]  # Consistent prefix
```

**In OpenAPI tags list**: Keep these adjacent for logical discovery.

### Pattern 2: Admin Versions of Public Resources

When you have both public and admin versions of a resource:

```python
# Public API
class UserController(Controller):
    tags = ["Users"]

# Admin API
class AdminUserController(Controller):
    tags = ["Admin Users"]  # Admin prefix, same concept
```

### Pattern 3: Unified Content Type

When multiple content types share a category (e.g., community posts, photos, videos):

```python
class CommunityPostController(Controller):
    tags = ["Community Content"]  # All use same tag

class CommunityPhotoController(Controller):
    tags = ["Community Content"]  # Grouped together

class CommunityVideoController(Controller):
    tags = ["Community Content"]  # Grouped together
```

## Troubleshooting

### Problem: Tags Not Appearing in Scalar UI

**Causes**:
1. Controller tags not updated
2. OpenAPI config not deployed
3. Browser cache issue

**Solutions**:
```bash
# 1. Verify controller tags
grep "tags = " src/pydotorg/domains/*/controllers*.py

# 2. Restart development server
make serve

# 3. Hard refresh browser
# On Chrome: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)

# 4. Check OpenAPI schema
curl http://localhost:8000/api/v1/openapi.json | jq '.tags'
```

### Problem: Duplicate Tags in Scalar UI

**Causes**:
1. Controller has multiple tags
2. Sub-controllers with overlapping tag assignments

**Solution**:
```python
# Each controller should have exactly one tag
class MyController(Controller):
    tags = ["Single Tag Only"]  # Not multiple

# If you need multiple concepts, create related tags
class UserController(Controller):
    tags = ["Users"]

class UserMembershipController(Controller):
    tags = ["User Memberships"]  # Related but distinct
```

### Problem: Tags Not in Expected Order

**Causes**:
1. Tag order in OpenAPI config doesn't match desired order
2. Scalar UI is using alphabetical ordering

**Solution**:
```python
# In openapi_tags.py, ensure tags are defined in desired order
OPENAPI_TAGS = [
    Tag(name="Authentication", ...),      # 1st
    Tag(name="Users", ...),               # 2nd
    Tag(name="User Memberships", ...),    # 3rd
    # ... in the correct order
]
```

Scalar respects the tag order defined in the OpenAPI spec.

## Future Improvements

### Potential Enhancements

1. **Tag Categories**: If the API grows significantly, consider grouping tags into categories (e.g., "Core", "Content", "Administration")

2. **Search-Friendly Tags**: Add searchable keywords to help developers find tags (may require custom Scalar configuration)

3. **Tag Aliases**: For tags with multiple names (e.g., "Python Releases" vs "Downloads"), consider supporting aliases

4. **Analytics Integration**: Track which tags developers use most to optimize tag organization

5. **Deprecation Warnings**: For tags/endpoints being deprecated, add deprecation markers in Scalar UI

## References

- Litestar OpenAPI Documentation: https://docs.litestar.dev/latest/features/openapi.html
- OpenAPI 3.1.0 Specification: https://spec.openapis.org/oas/v3.1.0
- Scalar API Documentation: https://scalar.com/
- This project's tag documentation:
  - `API_TAGS_STRUCTURE.md` - Detailed structure and rationale
  - `API_TAGS_QUICK_REF.md` - Quick reference table
  - `API_TAGS_HIERARCHY.txt` - Visual hierarchy
  - `API_TAGS_IMPLEMENTATION.md` - Implementation guide

:orphan:

# API Tags Implementation Guide

Step-by-step guide to implement the optimized tag structure in the Python.org Litestar API.

## Overview

This guide walks through migrating from the current fragmented tag structure to the optimized 50-tag hierarchy defined in `API_TAGS_STRUCTURE.md`.

## Phase 1: Audit Current Implementation

### 1.1 Identify All Current Tags

```bash
grep -rn "tags = " src/pydotorg/domains/*/controllers*.py | grep -o 'tags = \[.*\]'
```

Output should match `API_TAGS_QUICK_REF.md` table.

### 1.2 Verify Render Controllers

```bash
grep -rn "render" src/pydotorg/domains/*/controllers.py | grep "class\|tags = "
```

Should find:
- `JobRenderController` → `jobs/controllers.py:291`
- `NominationRenderController` → `nominations/controllers.py:248`
- `PageRenderController` → `pages/controllers.py:212`
- `SearchRenderController` → `search/controllers.py:77`
- `SponsorRenderController` → `sponsors/controllers.py:374`

## Phase 2: Update Controller Tags

### 2.1 Tag Migration Map

Update all controller files with consistent Title Case tag names:

```python
# src/pydotorg/domains/users/controllers.py

class UserController(Controller):
    # Before:
    tags = ["users"]
    # After:
    tags = ["Users"]

class MembershipController(Controller):
    # Before:
    tags = ["memberships"]
    # After:
    tags = ["User Memberships"]

class UserGroupController(Controller):
    # Before:
    tags = ["user-groups"]
    # After:
    tags = ["User Groups"]
```

### 2.2 Downloads Domain

```python
# src/pydotorg/domains/downloads/controllers.py

class OSController(Controller):
    # Before:
    tags = ["os"]
    # After:
    tags = ["Operating Systems"]

class ReleaseController(Controller):
    # Before:
    tags = ["releases"]
    # After:
    tags = ["Python Releases"]

class ReleaseFileController(Controller):
    # Before:
    tags = ["release-files"]
    # After:
    tags = ["Release Files"]
```

### 2.3 Events Domain

```python
# src/pydotorg/domains/events/controllers.py

class CalendarController(Controller):
    # Before:
    tags = ["calendars"]
    # After:
    tags = ["Event Calendars"]

class EventCategoryController(Controller):
    # Before:
    tags = ["event-categories"]
    # After:
    tags = ["Event Categories"]

class EventLocationController(Controller):
    # Before:
    tags = ["event-locations"]
    # After:
    tags = ["Event Locations"]

class EventOccurrenceController(Controller):
    # Before:
    tags = ["event-occurrences"]
    # After:
    tags = ["Event Occurrences"]

class EventController(Controller):
    # Before:
    tags = ["events"]
    # After:
    tags = ["Events"]
```

### 2.4 Jobs Domain

```python
# src/pydotorg/domains/jobs/controllers.py

class JobController(Controller):
    # Before:
    tags = ["jobs"]
    # After:
    tags = ["Jobs"]

class JobTypeController(Controller):
    # Before:
    tags = ["job-types"]
    # After:
    tags = ["Job Types"]

class JobCategoryController(Controller):
    # Before:
    tags = ["job-categories"]
    # After:
    tags = ["Job Categories"]

class JobReviewCommentController(Controller):
    # Before:
    tags = ["job-review-comments"]
    # After:
    tags = ["Job Review Comments"]

class JobRenderController(Controller):
    # Before:
    tags = ["jobs-render"]
    # After (EXCLUDE):
    tags = ["internal"]  # or include_in_schema=False
```

### 2.5 Sponsors Domain

```python
# src/pydotorg/domains/sponsors/controllers.py

class SponsorController(Controller):
    # Before:
    tags = ["sponsors"]
    # After:
    tags = ["Sponsors"]

class SponsorshipLevelController(Controller):
    # Before:
    tags = ["sponsorship-levels"]
    # After:
    tags = ["Sponsorship Levels"]

class SponsorshipController(Controller):
    # Before:
    tags = ["sponsorships"]
    # After:
    tags = ["Sponsorships"]

class SponsorRenderController(Controller):
    # Before:
    tags = ["sponsors-render"]
    # After (EXCLUDE):
    tags = ["internal"]
```

### 2.6 Blogs Domain

```python
# src/pydotorg/domains/blogs/controllers.py

class BlogEntryController(Controller):
    # Before:
    tags = ["blog-entries"]
    # After:
    tags = ["Blogs"]

class FeedController(Controller):
    # Before:
    tags = ["feeds"]
    # After:
    tags = ["Blog Feeds"]

class FeedAggregateController(Controller):
    # Before:
    tags = ["feed-aggregates"]
    # After:
    tags = ["Blog Feeds"]  # Merge with feeds

class RelatedBlogController(Controller):
    # Before:
    tags = ["related-blogs"]
    # After:
    tags = ["Blogs"]  # Merge with main blogs
```

### 2.7 Community Domain

```python
# src/pydotorg/domains/community/controllers.py

class CommunityGroupController(Controller):
    # Rename from "user-groups" endpoint specific
    tags = ["User Groups & Communities"]

class CommunityPostController(Controller):
    # Before:
    tags = ["community-posts"]
    # After:
    tags = ["Community Content"]

class CommunityPhotoController(Controller):
    # Before:
    tags = ["community-photos"]
    # After:
    tags = ["Community Content"]

class CommunityVideoController(Controller):
    # Before:
    tags = ["community-videos"]
    # After:
    tags = ["Community Content"]

class CommunityLinkController(Controller):
    # Before:
    tags = ["community-links"]
    # After:
    tags = ["Community Content"]
```

### 2.8 Success Stories Domain

```python
# src/pydotorg/domains/successstories/controllers.py

class SuccessStoryController(Controller):
    # Before:
    tags = ["success-stories"]
    # After:
    tags = ["Success Stories"]

class SuccessStoryCategoryController(Controller):
    # Before:
    tags = ["success-stories-categories"]
    # After:
    tags = ["Success Story Categories"]
```

### 2.9 Other Domains

```python
# src/pydotorg/domains/pages/controllers.py
class PageController(Controller):
    tags = ["Pages"]  # Before: "pages"

class PageRenderController(Controller):
    tags = ["internal"]  # Before: "page-render" (EXCLUDE)

# src/pydotorg/domains/banners/controllers.py
class BannerController(Controller):
    tags = ["Banners"]  # Before: "banners"

# src/pydotorg/domains/codesamples/controllers.py
class CodeSampleController(Controller):
    tags = ["Code Samples"]  # Before: "code-samples"

# src/pydotorg/domains/search/controllers.py
class SearchController(Controller):
    tags = ["Search"]  # Before: "search"

class SearchRenderController(Controller):
    tags = ["internal"]  # Before: "search-render" (EXCLUDE)

# src/pydotorg/domains/nominations/controllers.py
class NominationController(Controller):
    tags = ["Nominations"]  # Before: "nominations"

class NomineeController(Controller):
    tags = ["Nominees"]  # Before: "nominees"

class NominationRenderController(Controller):
    tags = ["internal"]  # Before: "nominations-render" (EXCLUDE)

# src/pydotorg/domains/minutes/controllers.py
class MinutesController(Controller):
    tags = ["Meeting Minutes"]  # Before: "minutes"

# src/pydotorg/domains/work_groups/controllers.py
class WorkGroupController(Controller):
    tags = ["Work Groups"]  # Before: "work-groups"

# src/pydotorg/domains/mailing/controllers.py
class MailingController(Controller):
    tags = ["Mailing Lists"]  # Before: check current
```

### 2.10 Admin Domain

All admin controllers should follow the pattern `"Admin *"`:

```python
# src/pydotorg/domains/admin/controllers/dashboard.py
class AdminDashboardController(Controller):
    tags = ["Admin Dashboard"]

# src/pydotorg/domains/admin/controllers/users.py
class AdminUserController(Controller):
    tags = ["Admin Users"]

# src/pydotorg/domains/admin/controllers/pages.py
class AdminPageController(Controller):
    tags = ["Admin Pages"]

# src/pydotorg/domains/admin/controllers/events.py
class AdminEventController(Controller):
    tags = ["Admin Events"]

# src/pydotorg/domains/admin/controllers/jobs.py
class AdminJobController(Controller):
    tags = ["Admin Jobs"]

# src/pydotorg/domains/admin/controllers/sponsors.py
class AdminSponsorController(Controller):
    tags = ["Admin Sponsors"]

# src/pydotorg/domains/admin/controllers/blogs.py
class AdminBlogController(Controller):
    tags = ["Admin Blogs"]

# src/pydotorg/domains/admin/controllers/logs.py
class AdminLogController(Controller):
    tags = ["Admin Logs"]

class AdminEmailTemplateController(Controller):
    tags = ["Admin Email Templates"]

class AdminEmailLogController(Controller):
    tags = ["Admin Email Logs"]

# src/pydotorg/domains/admin/controllers/tasks.py
class AdminTaskController(Controller):
    tags = ["Admin Tasks"]

# src/pydotorg/domains/admin/controllers/settings.py
class AdminSettingController(Controller):
    tags = ["Admin Settings"]
```

## Phase 3: Configure OpenAPI Tags

### 3.1 Create Tag Configuration

Create a new file to define all OpenAPI tags:

```python
# src/pydotorg/config/openapi_tags.py

from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Tag

OPENAPI_TAGS = [
    # Core API
    Tag(
        name="Authentication",
        description="User authentication, login, registration, and token management",
    ),
    Tag(
        name="Users",
        description="User account management, profiles, and account operations",
    ),
    Tag(
        name="User Memberships",
        description="User membership types and membership status management",
    ),
    Tag(
        name="User Groups",
        description="User group management, approval, and trust status",
    ),

    # Content Management
    Tag(
        name="Pages",
        description="Static pages and page management",
    ),
    Tag(
        name="Documents",
        description="Documentation files and document management",
    ),
    Tag(
        name="Images",
        description="Image assets and image management",
    ),
    Tag(
        name="Banners",
        description="Website banners and promotional content",
    ),
    Tag(
        name="Code Samples",
        description="Code examples and sample snippets",
    ),

    # Downloads & Releases
    Tag(
        name="Operating Systems",
        description="Supported operating systems for Python downloads",
    ),
    Tag(
        name="Python Releases",
        description="Python version releases and release information",
    ),
    Tag(
        name="Release Files",
        description="Download files associated with Python releases",
    ),

    # Events & Community
    Tag(
        name="Events",
        description="Python events and conference information",
    ),
    Tag(
        name="Event Calendars",
        description="Event calendars and calendar management",
    ),
    Tag(
        name="Event Categories",
        description="Event type categories and classifications",
    ),
    Tag(
        name="Event Locations",
        description="Physical venues and event locations",
    ),
    Tag(
        name="Event Occurrences",
        description="Specific event instances and scheduling",
    ),
    Tag(
        name="User Groups & Communities",
        description="Community groups and member organizations",
    ),
    Tag(
        name="Community Content",
        description="Community-contributed content (posts, photos, videos, links)",
    ),

    # Content Discovery
    Tag(
        name="Blogs",
        description="Blog posts and blog entries",
    ),
    Tag(
        name="Blog Feeds",
        description="RSS feeds and feed aggregation",
    ),
    Tag(
        name="Success Stories",
        description="User success stories and testimonials",
    ),
    Tag(
        name="Success Story Categories",
        description="Success story categories and classifications",
    ),

    # Jobs & Opportunities
    Tag(
        name="Jobs",
        description="Python job listings and employment opportunities",
    ),
    Tag(
        name="Job Types",
        description="Job type categories (contract, full-time, part-time, etc.)",
    ),
    Tag(
        name="Job Categories",
        description="Job industry and role categories",
    ),
    Tag(
        name="Job Review Comments",
        description="Job listing review comments and moderation",
    ),

    # Business & Sponsorship
    Tag(
        name="Sponsors",
        description="Python organizations and sponsor information",
    ),
    Tag(
        name="Sponsorship Levels",
        description="Sponsorship tier definitions and benefits",
    ),
    Tag(
        name="Sponsorships",
        description="Active sponsorship relationships and agreements",
    ),
    Tag(
        name="Companies",
        description="Company profiles and organization data",
    ),

    # Governance & Meetings
    Tag(
        name="Work Groups",
        description="Python Enhancement Proposal (PEP) work groups",
    ),
    Tag(
        name="Meeting Minutes",
        description="Meeting notes and minutes archives",
    ),
    Tag(
        name="Nominations",
        description="Award nominations and election cycles",
    ),
    Tag(
        name="Nominees",
        description="Nominated individuals and candidates",
    ),
    Tag(
        name="Elections",
        description="Election information and voting",
    ),

    # Discovery & Utilities
    Tag(
        name="Search",
        description="Full-text and faceted search across platform",
    ),
    Tag(
        name="Mailing Lists",
        description="Email list subscriptions and management",
    ),

    # Administration
    Tag(
        name="Admin Dashboard",
        description="Administrative dashboard and system overview",
    ),
    Tag(
        name="Admin Users",
        description="Administrative user management",
    ),
    Tag(
        name="Admin Pages",
        description="Administrative page management",
    ),
    Tag(
        name="Admin Events",
        description="Administrative event management",
    ),
    Tag(
        name="Admin Jobs",
        description="Administrative job listing management",
    ),
    Tag(
        name="Admin Sponsors",
        description="Administrative sponsor management",
    ),
    Tag(
        name="Admin Blogs",
        description="Administrative blog management",
    ),
    Tag(
        name="Admin Logs",
        description="System logging and audit trails",
    ),
    Tag(
        name="Admin Email Templates",
        description="Email template management and customization",
    ),
    Tag(
        name="Admin Email Logs",
        description="Email delivery logs and status tracking",
    ),
    Tag(
        name="Admin Tasks",
        description="Background task management and scheduling",
    ),
    Tag(
        name="Admin Settings",
        description="System configuration and application settings",
    ),
]
```

### 3.2 Update Application Configuration

```python
# src/pydotorg/config.py or src/pydotorg/main.py

from pydotorg.config.openapi_tags import OPENAPI_TAGS
from litestar.openapi.config import OpenAPIConfig

app = Litestar(
    route_handlers=[...],
    openapi_config=OpenAPIConfig(
        title="Python.org API",
        version="1.0.0",
        tags=OPENAPI_TAGS,  # Add this
    ),
    # ... rest of config
)
```

## Phase 4: Exclude Render Controllers

### 4.1 Option A: Mark as Internal

For controllers that serve HTML rendering and shouldn't appear in public API docs:

```python
# src/pydotorg/domains/jobs/controllers.py

class JobRenderController(Controller):
    path = "/jobs"
    tags = ["internal"]  # Will be filtered out in OpenAPI
    include_in_schema = False  # Explicitly exclude from OpenAPI schema

    # ... routes
```

### 4.2 Option B: Filter in OpenAPI Config

Alternatively, filter tags in the OpenAPI configuration:

```python
# src/pydotorg/config.py

from litestar.openapi.config import OpenAPIConfig

# Filter out internal and render controllers
excluded_tags = {"internal", "admin-internal"}

openapi_config = OpenAPIConfig(
    title="Python.org API",
    version="1.0.0",
    tags=OPENAPI_TAGS,
    # Custom filter logic (may need to implement in Litestar)
)
```

## Phase 5: Testing & Validation

### 5.1 Test Tag Organization

```bash
# Run tests to verify tags are properly assigned
uv run pytest tests/ -v -k "tag" --no-cov

# Check OpenAPI schema generation
uv run pytest tests/integration/test_openapi.py -v
```

### 5.2 Validate in Scalar UI

1. Start the development server: `make serve`
2. Visit the API documentation (typically `http://localhost:8000/docs`)
3. Verify:
   - Tags appear in the left sidebar
   - Tags are in the correct order
   - Render controllers are hidden
   - Admin tags are grouped together
   - Tag descriptions are clear and helpful

### 5.3 Manual Verification

Confirm all tag updates:

```bash
# Check all tags are updated
grep -rn "tags = " src/pydotorg/domains/*/controllers*.py | \
  grep -v "tags = \[\"[A-Z]" | \
  grep -v "tags = \[\"Admin" | \
  grep -v "tags = \[\"internal"

# Should return no results (all tags properly cased)
```

## Phase 6: Documentation

### 6.1 Update API Documentation

Add to the main API documentation:
- Link to `API_TAGS_STRUCTURE.md` for detailed tag information
- Include quick reference table from `API_TAGS_QUICK_REF.md`
- Show visual hierarchy from `API_TAGS_HIERARCHY.txt`

### 6.2 Update Developer Guides

- Update any developer onboarding docs to reference new tag structure
- Add tag navigation tips to API documentation
- Document any tag-specific conventions

### 6.3 Communicate Changes

- Notify API users about the new tag structure
- Highlight improvements in API documentation UX
- Provide migration guide for any dependent systems

## Checklist

- [ ] Review and approve tag structure
- [ ] Update all controller `tags` assignments (Phase 2)
- [ ] Create OpenAPI tag configuration (Phase 3.1)
- [ ] Update application configuration (Phase 3.2)
- [ ] Mark/exclude render controllers (Phase 4)
- [ ] Run tag-related tests (Phase 5.1)
- [ ] Validate in Scalar UI (Phase 5.2)
- [ ] Verify all tags are properly formatted (Phase 5.3)
- [ ] Update API documentation (Phase 6.1)
- [ ] Update developer guides (Phase 6.2)
- [ ] Communicate changes to stakeholders (Phase 6.3)
- [ ] Monitor usage patterns post-launch

## Rollback Plan

If issues arise after implementation:

```bash
# Revert controller tag changes
git checkout -- src/pydotorg/domains/*/controllers*.py

# Revert configuration changes
git checkout -- src/pydotorg/config/openapi_tags.py
git checkout -- src/pydotorg/config.py
```

## References

- `API_TAGS_STRUCTURE.md` - Detailed tag definitions and rationale
- `API_TAGS_QUICK_REF.md` - Quick reference table
- `API_TAGS_HIERARCHY.txt` - Visual tag hierarchy diagram
- Scalar Documentation: https://scalar.com/
- Litestar OpenAPI: https://docs.litestar.dev/latest/features/openapi.html

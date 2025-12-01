# API Tags - Quick Reference

Mapping of Python.org API resources to recommended tag categories.

## Tag Reference Table

| # | Tag Name | Resource Controllers | Key Endpoints |
|---|----------|----------------------|----------------|
| 1 | Authentication | `users/auth_controller.py` | Login, register, token, password reset |
| 2 | Users | `users/controllers.py:UserController` | List, get, create, update, deactivate user |
| 3 | User Memberships | `users/controllers.py:MembershipController` | List, get, create, update membership |
| 4 | User Groups | `users/controllers.py:UserGroupController` | List, create, approve, trust management |
| 5 | Pages | `pages/controllers.py` | List, get page, create, update, delete |
| 6 | Documents | `docs/controllers.py` | List, get, upload, delete documents |
| 7 | Images | Image controllers | List, upload, delete images |
| 8 | Banners | `banners/controllers.py` | List, get, create, update banners |
| 9 | Code Samples | `codesamples/controllers.py` | List, create, delete code samples |
| 10 | Operating Systems | `downloads/controllers.py:OSController` | List OS, get by slug |
| 11 | Python Releases | `downloads/controllers.py:ReleaseController` | List, get release, latest version |
| 12 | Release Files | `downloads/controllers.py:ReleaseFileController` | List, get, upload files |
| 13 | Events | `events/controllers.py:EventController` | List, get, upcoming events |
| 14 | Event Calendars | `events/controllers.py:CalendarController` | List, get calendar, create, update |
| 15 | Event Categories | `events/controllers.py:EventCategoryController` | List, create, update categories |
| 16 | Event Locations | `events/controllers.py:EventLocationController` | List, get, create, update locations |
| 17 | Event Occurrences | `events/controllers.py:EventOccurrenceController` | List, get, create occurrences |
| 18 | User Groups & Communities | `community/controllers.py` | List groups, discovery |
| 19 | Community Content | `community/controllers.py` (sub) | Posts, photos, videos, links |
| 20 | Blogs | `blogs/controllers.py` | List, get, create blog entries |
| 21 | Blog Feeds | `blogs/controllers.py:FeedController` | List, create, manage feeds |
| 22 | Success Stories | `successstories/controllers.py` | List, get, create stories |
| 23 | Success Story Categories | `successstories/controllers.py` | List, manage categories |
| 24 | Jobs | `jobs/controllers.py:JobController` | List, get, search, post jobs |
| 25 | Job Types | `jobs/controllers.py:JobTypeController` | List, create job types |
| 26 | Job Categories | `jobs/controllers.py:JobCategoryController` | List, create categories |
| 27 | Job Review Comments | `jobs/controllers.py:JobReviewCommentController` | List, add, delete comments |
| 28 | Sponsors | `sponsors/controllers.py:SponsorController` | List, get sponsor info |
| 29 | Sponsorship Levels | `sponsors/controllers.py:SponsorshipLevelController` | List, manage levels |
| 30 | Sponsorships | `sponsors/controllers.py:SponsorshipController` | List, manage sponsorships |
| 31 | Companies | `companies/controllers.py` | List, get, search companies |
| 32 | Work Groups | `work_groups/controllers.py` | List, get group info |
| 33 | Meeting Minutes | `minutes/controllers.py` | List, get, archive minutes |
| 34 | Nominations | `nominations/controllers.py:NominationController` | List, submit nominations |
| 35 | Nominees | `nominations/controllers.py:NomineeController` | List, get nominee details |
| 36 | Elections | `nominations/controllers.py:ElectionController` | List, get election info |
| 37 | Search | `search/controllers.py` | Search, facets, suggestions |
| 38 | Mailing Lists | `mailing/controllers.py` | Subscribe, manage preferences |
| 39 | Admin Dashboard | `admin/controllers/dashboard.py` | Stats, health, overview |
| 40 | Admin Users | `admin/controllers/users.py` | Manage users, permissions |
| 41 | Admin Pages | `admin/controllers/pages.py` | Manage, bulk operations |
| 42 | Admin Events | `admin/controllers/events.py` | Approve, moderate |
| 43 | Admin Jobs | `admin/controllers/jobs.py` | Moderate, approve, manage |
| 44 | Admin Sponsors | `admin/controllers/sponsors.py` | Manage sponsorships |
| 45 | Admin Blogs | `admin/controllers/blogs.py` | Manage, moderate |
| 46 | Admin Logs | `admin/controllers/logs.py` | View logs, audit trails |
| 47 | Admin Email Templates | Email template controller | Manage templates |
| 48 | Admin Email Logs | Email log controller | View delivery logs |
| 49 | Admin Tasks | `admin/controllers/tasks.py` | Manage background tasks |
| 50 | Admin Settings | `admin/controllers/settings.py` | System configuration |

## Render Controllers (Exclude from Public API Docs)

These controllers serve HTML pages and should NOT appear in the public API documentation:

- `jobs/controllers.py:JobRenderController` → tags = "internal"
- `nominations/controllers.py:NominationRenderController` → tags = "internal"
- `pages/controllers.py:PageRenderController` → tags = "internal"
- `search/controllers.py:SearchRenderController` → tags = "internal"
- `sponsors/controllers.py:SponsorRenderController` → tags = "internal"

## Tag Groups by Category

### Core (6 tags)
Authentication, Users, User Memberships, User Groups, Search, Mailing Lists

### Content (4 tags)
Pages, Documents, Images, Banners, Code Samples

### Downloads (3 tags)
Operating Systems, Python Releases, Release Files

### Events (5 tags)
Events, Event Calendars, Event Categories, Event Locations, Event Occurrences

### Community (2 tags)
User Groups & Communities, Community Content

### Content Discovery (3 tags)
Blogs, Blog Feeds, Success Stories, Success Story Categories

### Jobs (4 tags)
Jobs, Job Types, Job Categories, Job Review Comments

### Business (4 tags)
Sponsors, Sponsorship Levels, Sponsorships, Companies

### Governance (5 tags)
Work Groups, Meeting Minutes, Nominations, Nominees, Elections

### Administration (12 tags)
Admin Dashboard, Admin Users, Admin Pages, Admin Events, Admin Jobs, Admin Sponsors, Admin Blogs, Admin Logs, Admin Email Templates, Admin Email Logs, Admin Tasks, Admin Settings

## Implementation Checklist

- [ ] Review tag structure with team
- [ ] Update all controller `tags = ["old-tag"]` to `tags = ["New Tag Name"]`
- [ ] Configure OpenAPI tags in main application
- [ ] Add exclude mechanism for render controllers
- [ ] Test in Scalar UI with live API
- [ ] Update API documentation
- [ ] Brief developers on new structure
- [ ] Monitor analytics for usage patterns

## Common Migration Examples

```text
# Before                           After
tags = ["users"]                   tags = ["Users"]
tags = ["memberships"]             tags = ["User Memberships"]
tags = ["user-groups"]             tags = ["User Groups"]
tags = ["releases"]                tags = ["Python Releases"]
tags = ["release-files"]           tags = ["Release Files"]
tags = ["job-types"]               tags = ["Job Types"]
tags = ["job-categories"]          tags = ["Job Categories"]
tags = ["job-review-comments"]     tags = ["Job Review Comments"]
tags = ["event-categories"]        tags = ["Event Categories"]
tags = ["event-locations"]         tags = ["Event Locations"]
tags = ["event-occurrences"]       tags = ["Event Occurrences"]
tags = ["blog-entries"]            tags = ["Blogs"]
tags = ["feed-aggregates"]         tags = ["Blog Feeds"]
tags = ["community-posts"]         tags = ["Community Content"]
tags = ["community-photos"]        tags = ["Community Content"]
tags = ["success-stories"]         tags = ["Success Stories"]
tags = ["sponsorship-levels"]      tags = ["Sponsorship Levels"]
tags = ["code-samples"]            tags = ["Code Samples"]
tags = ["jobs-render"]             tags = ["internal"] (exclude)
tags = ["page-render"]             tags = ["internal"] (exclude)
tags = ["search-render"]           tags = ["internal"] (exclude)
```

## Notes

- All tags use Title Case with Spaces (more readable in Scalar UI)
- Render controllers use "internal" tag and should be excluded from public schema
- Admin tags are grouped under "Admin *" prefix for easy filtering
- Related resources are adjacent in the list for logical discovery
- Total of 50 public tags (down from 100+), much more navigable

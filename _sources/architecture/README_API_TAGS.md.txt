:orphan:

# API Tags Documentation

Complete documentation for the Python.org API OpenAPI tag structure optimization.

## Overview

This directory contains comprehensive documentation for the redesigned OpenAPI tag hierarchy for the Python.org API. The new structure reduces 100+ fragmented tags down to 50 logically grouped, consistently named tags that improve developer experience in the Scalar API documentation UI.

## Files in This Directory

### Start Here
- **API_TAGS_SUMMARY.txt** - Executive summary with statistics and overview
- **API_TAGS_INDEX.md** - Navigation guide and reading recommendations

### For Implementation
- **API_TAGS_IMPLEMENTATION.md** - Step-by-step implementation guide with code examples
- **API_TAGS_QUICK_REF.md** - Quick reference table for tag assignments

### For Understanding
- **API_TAGS_STRUCTURE.md** - Complete tag definitions and rationale
- **API_TAGS_HIERARCHY.txt** - Visual ASCII diagram showing tag relationships

### For Maintenance
- **API_TAGS_BEST_PRACTICES.md** - Guidelines for adding/maintaining tags

## Quick Facts

| Metric | Value |
|--------|-------|
| Total Tags | 50 public + 1 internal + render exclusions |
| Tag Reduction | From 100+ to 50 (50% reduction) |
| Documentation Size | 112 KB total |
| Implementation Time | 4-6 hours |
| Testing Time | 2-3 hours |
| Controllers to Update | 27 files |
| Render Controllers (excluded) | 5 |

## Getting Started

### I Want to Understand the Big Picture
1. Read **API_TAGS_SUMMARY.txt** (5 minutes)
2. View **API_TAGS_HIERARCHY.txt** (10 minutes)
3. Skim **API_TAGS_QUICK_REF.md** table (5 minutes)

### I Need to Implement This
1. Read **API_TAGS_QUICK_REF.md** (5 minutes)
2. Follow **API_TAGS_IMPLEMENTATION.md** (4-6 hours)
3. Reference **API_TAGS_BEST_PRACTICES.md** as needed

### I'm Adding New Tags or Maintaining the Structure
1. Review **API_TAGS_BEST_PRACTICES.md** (15 minutes)
2. Check **API_TAGS_QUICK_REF.md** for existing tags
3. Use naming conventions from "Best Practices"

### I Want All the Details
1. **API_TAGS_INDEX.md** - Overview and navigation
2. **API_TAGS_STRUCTURE.md** - Detailed definitions
3. **API_TAGS_HIERARCHY.txt** - Visual relationships
4. **API_TAGS_IMPLEMENTATION.md** - How to build it
5. **API_TAGS_BEST_PRACTICES.md** - How to maintain it

## The 50-Tag Structure

### Core (6 tags)
Authentication, Users, User Memberships, User Groups, Search, Mailing Lists

### Content (5 tags)
Pages, Documents, Images, Banners, Code Samples

### Downloads (3 tags)
Operating Systems, Python Releases, Release Files

### Events (7 tags)
Events, Event Calendars, Event Categories, Event Locations, Event Occurrences, User Groups & Communities, Community Content

### Discovery (4 tags)
Blogs, Blog Feeds, Success Stories, Success Story Categories

### Jobs (4 tags)
Jobs, Job Types, Job Categories, Job Review Comments

### Business (4 tags)
Sponsors, Sponsorship Levels, Sponsorships, Companies

### Governance (5 tags)
Work Groups, Meeting Minutes, Nominations, Nominees, Elections

### Admin (12 tags)
Admin Dashboard, Admin Users, Admin Pages, Admin Events, Admin Jobs, Admin Sponsors, Admin Blogs, Admin Logs, Admin Email Templates, Admin Email Logs, Admin Tasks, Admin Settings

## Key Improvements

1. **50% Fewer Tags** - Reduced from 100+ to 50 for easier navigation
2. **Consistent Naming** - Title Case with spaces (not kebab-case)
3. **Logical Grouping** - Related endpoints grouped by business domain
4. **Admin Isolation** - 12 distinct admin tags instead of generic "Admin"
5. **Render Exclusion** - HTML controllers hidden from public API docs
6. **Developer Journey** - Ordered by typical API consumption flow

## Implementation Phases

1. **Audit** - Identify current tags and structure
2. **Update** - Change controller tags and consolidate
3. **Configure** - Set up OpenAPI tag definitions
4. **Exclude** - Mark render controllers as internal
5. **Test** - Validate in Scalar UI and test suite
6. **Deploy** - Roll out to production
7. **Document** - Update external documentation

See **API_TAGS_IMPLEMENTATION.md** for detailed steps.

## File Purposes at a Glance

```
API_TAGS_SUMMARY.txt
├─ Executive summary
├─ Key statistics
├─ Controller mapping changes
└─ Success criteria

API_TAGS_INDEX.md
├─ Navigation guide
├─ Reading recommendations by audience
├─ FAQs
└─ Contact info

API_TAGS_STRUCTURE.md
├─ All 50 tags with descriptions
├─ Design principles
├─ Ordering strategy
└─ Migration notes

API_TAGS_QUICK_REF.md
├─ Reference table (tag # → name → controllers)
├─ Tag groups by category
├─ Render controllers list
└─ Implementation checklist

API_TAGS_HIERARCHY.txt
├─ Visual ASCII diagram
├─ Hierarchical relationships
├─ Nesting structure
└─ Benefits summary

API_TAGS_IMPLEMENTATION.md
├─ Phase-by-phase guide
├─ Code examples for each domain
├─ OpenAPI configuration template
├─ Testing procedures
└─ Rollback plan

API_TAGS_BEST_PRACTICES.md
├─ Naming conventions
├─ Controller organization
├─ When to add/refactor tags
├─ Testing guidelines
├─ Common patterns
└─ Troubleshooting
```

## Current Status

- **Design**: Complete
- **Documentation**: Complete (7 files)
- **Implementation**: Ready to begin
- **Testing**: Procedures documented
- **Rollback Plan**: Prepared

## Next Steps

1. Review this documentation
2. Get team approval on the structure
3. Begin implementation following API_TAGS_IMPLEMENTATION.md
4. Test in Scalar UI
5. Deploy to production

## Questions?

Refer to **API_TAGS_INDEX.md** for FAQs and detailed guidance.

## Document Tree

```
docs/architecture/
├── README_API_TAGS.md              ← You are here
├── API_TAGS_SUMMARY.txt            (Executive summary)
├── API_TAGS_INDEX.md               (Navigation & overview)
├── API_TAGS_STRUCTURE.md           (Detailed definitions)
├── API_TAGS_QUICK_REF.md           (Quick reference)
├── API_TAGS_HIERARCHY.txt          (Visual diagram)
├── API_TAGS_IMPLEMENTATION.md      (Implementation guide)
└── API_TAGS_BEST_PRACTICES.md      (Maintenance guide)
```

---

**Total Documentation**: 8 files | 112 KB | ~100 minutes read time

**Start with**: API_TAGS_SUMMARY.txt (5 min) then API_TAGS_QUICK_REF.md (5 min)

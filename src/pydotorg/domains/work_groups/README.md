# Work Groups Domain

Domain for managing Python work groups and special interest groups.

## Models

- **WorkGroup**: Work groups with name, purpose, activity status, and external URLs

## API Endpoints

- `GET /api/v1/work-groups` - List all work groups
- `GET /api/v1/work-groups/{work_group_id}` - Get work group by ID
- `GET /api/v1/work-groups/slug/{slug}` - Get work group by slug
- `GET /api/v1/work-groups/active` - List active work groups
- `POST /api/v1/work-groups` - Create new work group
- `PUT /api/v1/work-groups/{work_group_id}` - Update work group
- `DELETE /api/v1/work-groups/{work_group_id}` - Delete work group

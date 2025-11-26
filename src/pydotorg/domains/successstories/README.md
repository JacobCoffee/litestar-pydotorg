# Success Stories Domain

Domain for managing Python success stories and story categories.

## Models

- **StoryCategory**: Categories for organizing success stories
- **Story**: Success stories featuring Python usage in companies and projects

## API Endpoints

### Categories
- `GET /api/v1/success-stories/categories` - List all categories
- `GET /api/v1/success-stories/categories/{category_id}` - Get category by ID
- `GET /api/v1/success-stories/categories/slug/{slug}` - Get category by slug
- `POST /api/v1/success-stories/categories` - Create new category
- `PUT /api/v1/success-stories/categories/{category_id}` - Update category
- `DELETE /api/v1/success-stories/categories/{category_id}` - Delete category

### Stories
- `GET /api/v1/success-stories` - List all stories
- `GET /api/v1/success-stories/{story_id}` - Get story by ID
- `GET /api/v1/success-stories/slug/{slug}` - Get story by slug
- `GET /api/v1/success-stories/published` - List published stories
- `GET /api/v1/success-stories/featured` - List featured stories
- `GET /api/v1/success-stories/category/{category_id}` - List stories by category
- `POST /api/v1/success-stories` - Create new story
- `PUT /api/v1/success-stories/{story_id}` - Update story
- `DELETE /api/v1/success-stories/{story_id}` - Delete story

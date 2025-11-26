# Community Domain

Domain for managing community posts, photos, videos, and links.

## Models

- **Post**: Community posts with title, content, and media attachments
- **Photo**: Images that can be standalone or attached to posts
- **Video**: Videos that can be standalone or attached to posts
- **Link**: Links that can be standalone or attached to posts

## API Endpoints

### Posts
- `GET /api/v1/community/posts` - List all posts
- `GET /api/v1/community/posts/{post_id}` - Get post by ID
- `GET /api/v1/community/posts/slug/{slug}` - Get post by slug
- `GET /api/v1/community/posts/published` - List published posts
- `POST /api/v1/community/posts` - Create new post
- `PUT /api/v1/community/posts/{post_id}` - Update post
- `DELETE /api/v1/community/posts/{post_id}` - Delete post

### Photos
- `GET /api/v1/community/photos` - List all photos
- `GET /api/v1/community/photos/{photo_id}` - Get photo by ID
- `POST /api/v1/community/photos` - Create new photo
- `PUT /api/v1/community/photos/{photo_id}` - Update photo
- `DELETE /api/v1/community/photos/{photo_id}` - Delete photo

### Videos
- `GET /api/v1/community/videos` - List all videos
- `GET /api/v1/community/videos/{video_id}` - Get video by ID
- `POST /api/v1/community/videos` - Create new video
- `PUT /api/v1/community/videos/{video_id}` - Update video
- `DELETE /api/v1/community/videos/{video_id}` - Delete video

### Links
- `GET /api/v1/community/links` - List all links
- `GET /api/v1/community/links/{link_id}` - Get link by ID
- `POST /api/v1/community/links` - Create new link
- `PUT /api/v1/community/links/{link_id}` - Update link
- `DELETE /api/v1/community/links/{link_id}` - Delete link

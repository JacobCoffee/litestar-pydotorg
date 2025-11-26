# Banners Domain

Domain for managing site-wide banners and announcements.

## Models

- **Banner**: Site banners with title, message, activation status, and date ranges

## API Endpoints

- `GET /api/v1/banners` - List all banners
- `GET /api/v1/banners/{banner_id}` - Get banner by ID
- `GET /api/v1/banners/name/{name}` - Get banner by name
- `GET /api/v1/banners/active` - List active banners
- `POST /api/v1/banners` - Create new banner
- `PUT /api/v1/banners/{banner_id}` - Update banner
- `DELETE /api/v1/banners/{banner_id}` - Delete banner

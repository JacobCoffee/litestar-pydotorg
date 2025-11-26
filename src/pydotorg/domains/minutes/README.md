# Minutes Domain

Domain for managing meeting minutes.

## Models

- **Minutes**: Meeting minutes with date, content, and publication status

## API Endpoints

- `GET /api/v1/minutes` - List all minutes
- `GET /api/v1/minutes/{minutes_id}` - Get minutes by ID
- `GET /api/v1/minutes/slug/{slug}` - Get minutes by slug
- `GET /api/v1/minutes/published` - List published minutes
- `GET /api/v1/minutes/date/{date}` - Get minutes by date
- `POST /api/v1/minutes` - Create new minutes
- `PUT /api/v1/minutes/{minutes_id}` - Update minutes
- `DELETE /api/v1/minutes/{minutes_id}` - Delete minutes

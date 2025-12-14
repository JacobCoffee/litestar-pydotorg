:orphan:

# Postman Collection Guide

This guide explains how to use the Postman collection for the Litestar-pydotorg API.

## Quick Start

### 1. Import the Collection

1. Open Postman
2. Click **Import** in the top left
3. Select **File** and choose `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/docs/postman-collection.json`
4. Click **Import**

### 2. Configure Environment Variables

The collection uses the following variables:

- `base_url`: Default is `http://localhost:8000` (modify if needed)
- `access_token`: Automatically populated after login

To view/edit variables:
1. Click on the collection name "Litestar-pydotorg API"
2. Go to the **Variables** tab
3. Update `base_url` if your API runs on a different host/port

### 3. Authentication Workflow

#### Step 1: Register a User
```
POST /api/auth/register
```
Creates a new user account. Use the example request body and modify as needed.

#### Step 2: Login
```
POST /api/auth/login
```
Authenticates and receives an access token. The token is **automatically saved** to the `access_token` variable via a post-request script.

#### Step 3: Use Protected Endpoints
All subsequent requests will automatically include the Bearer token in the Authorization header.

### 4. Testing the Collection

Each request includes automated tests that:
- Verify response status codes
- Check response structure
- Validate data types
- Perform domain-specific checks

View test results in the **Test Results** tab after each request.

## Collection Structure

### Authentication Folder
- **Register**: Create new user account
- **Login**: Authenticate and get access token (auto-saves token)
- **Get Current User**: Retrieve authenticated user info
- **Refresh Token**: Refresh the access token
- **Logout**: End session and invalidate token

### Users Folder
- **List Users**: Paginated user list (with limit/offset)
- **Get User by ID**: Single user details
- **Create User**: Create new user (admin)
- **Update User**: Modify user information
- **Delete User**: Remove user account
- **Deactivate User**: Disable user account
- **Reactivate User**: Re-enable user account

### Jobs Folder
- **List Jobs**: Paginated job listings
- **Get Job by ID**: Single job details
- **Create Job**: Post new job listing
- **Submit Job for Review**: Submit draft for approval
- **Approve Job**: Approve pending job (admin)
- **Reject Job**: Reject pending job (admin)
- **Archive Job**: Archive expired job
- **My Jobs**: Get current user's job postings

### Events Folder
- **List Events**: Paginated event list
- **Get Featured Events**: Featured events only
- **Get Upcoming Events**: Future events with date validation
- **Get Event by ID**: Single event details
- **Create Event**: Create new event

### Search Folder
- **Search Jobs**: Full-text search with filters

## Features

### Automatic Token Management
The collection includes pre-request and post-request scripts that:
- Automatically inject Bearer tokens for authenticated requests
- Save access tokens from login responses
- Clear tokens on logout

### Request Validation
All requests include tests for:
- HTTP status codes
- Response structure
- Required fields
- Data type validation

### Example Request Bodies
Every POST/PUT/PATCH request includes a realistic example body with proper JSON structure.

## Common Workflows

### Workflow 1: Create and Submit a Job
1. Login → Save token
2. Create Job → Get job_id from response
3. Submit Job for Review → Use job_id
4. (Admin) Approve Job

### Workflow 2: User Management
1. Login as admin → Save token
2. List Users → See all users
3. Get User by ID → View details
4. Deactivate User → Disable account
5. Reactivate User → Re-enable account

### Workflow 3: Event Discovery
1. Get Featured Events → See promoted events
2. Get Upcoming Events → Find future events
3. Get Event by ID → View full details

## Tips

1. **Variable Reuse**: Save frequently used IDs as collection variables for quick access
2. **Test Environment**: Use different environments for local/staging/production
3. **Run Collection**: Use Collection Runner to execute all requests sequentially
4. **Monitor**: Set up Postman Monitors for API health checks

## Troubleshooting

### 401 Unauthorized
- Check that you've logged in and the `access_token` variable is set
- Token may have expired - try logging in again

### 404 Not Found
- Verify the API server is running on `http://localhost:8000`
- Check that resource IDs (UUIDs) are valid

### 422 Validation Error
- Review request body for required fields
- Check data types match the schema

## Additional Resources

- API Documentation: Check `/docs` endpoint (Swagger UI)
- OpenAPI Schema: Available at `/schema/openapi.json`
- Redoc: Alternative docs at `/redoc`

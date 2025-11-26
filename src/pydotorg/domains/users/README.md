# Users Domain

The Users domain handles user management, memberships, authentication, and user group management for the Python.org platform.

## Purpose

This domain provides:
- User account management (create, read, update, delete)
- User authentication and authorization (login, register, token refresh)
- Membership management for PSF members
- User group management with approval and trust workflows

## Models

### User
The core user model containing:
- Basic information (username, email, first/last name)
- Authentication data (password hash, is_active, is_staff, is_superuser)
- Profile information (bio, location, website)
- Privacy settings (email_privacy, search_visibility)
- Activity tracking (date_joined, last_login)

### Membership
PSF membership information:
- Membership type (BASIC, SUPPORTING, MANAGING, CONTRIBUTING, FELLOW)
- Creator and PSF member flags
- Votes cast tracking
- Legal and license agreement acceptance
- Associated user relationship

### UserGroup
Community user groups with:
- Group type (USER_GROUP, GOOGLE_GROUP, MAILING_LIST)
- Name and description
- Contact information (email, IRC, Jabber, Zulip)
- Moderation flags (is_approved, is_trusted)
- External links (website, mailing list URL)

## Endpoints

### User Endpoints
- `GET /api/v1/users` - List all users with pagination
- `GET /api/v1/users/{user_id}` - Get user by ID
- `GET /api/v1/users/username/{username}` - Get user by username
- `GET /api/v1/users/email/{email}` - Get user by email
- `POST /api/v1/users` - Create new user
- `PUT /api/v1/users/{user_id}` - Update user
- `PATCH /api/v1/users/{user_id}/deactivate` - Deactivate user account
- `PATCH /api/v1/users/{user_id}/reactivate` - Reactivate user account
- `DELETE /api/v1/users/{user_id}` - Delete user

### Authentication Endpoints
- `POST /api/auth/register` - Register new user account
- `POST /api/auth/login` - Login with username/password
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout (requires authentication)
- `POST /api/auth/me` - Get current user info (requires authentication)

### Membership Endpoints
- `GET /api/v1/memberships` - List all memberships with pagination
- `GET /api/v1/memberships/{membership_id}` - Get membership by ID
- `GET /api/v1/memberships/user/{user_id}` - Get membership by user ID
- `POST /api/v1/memberships` - Create new membership
- `PUT /api/v1/memberships/{membership_id}` - Update membership
- `DELETE /api/v1/memberships/{membership_id}` - Delete membership

### User Group Endpoints
- `GET /api/v1/user-groups` - List all user groups with pagination
- `GET /api/v1/user-groups/approved` - List approved user groups
- `GET /api/v1/user-groups/trusted` - List trusted user groups
- `GET /api/v1/user-groups/{group_id}` - Get user group by ID
- `POST /api/v1/user-groups` - Create new user group
- `PUT /api/v1/user-groups/{group_id}` - Update user group
- `PATCH /api/v1/user-groups/{group_id}/approve` - Approve a user group
- `PATCH /api/v1/user-groups/{group_id}/revoke-approval` - Revoke approval
- `PATCH /api/v1/user-groups/{group_id}/mark-trusted` - Mark as trusted
- `PATCH /api/v1/user-groups/{group_id}/revoke-trust` - Revoke trust
- `DELETE /api/v1/user-groups/{group_id}` - Delete user group

## Usage Examples

### Creating a User
```python
from pydotorg.domains.users import UserService, UserCreate

user_data = UserCreate(
    username="johndoe",
    email="john@example.com",
    password="SecurePass123!",
    first_name="John",
    last_name="Doe"
)

user = await user_service.create_user(user_data)
```

### Authentication
```python
from pydotorg.core.auth.schemas import LoginRequest

login_data = LoginRequest(
    username="johndoe",
    password="SecurePass123!"
)

# Returns TokenResponse with access_token and refresh_token
token_response = await auth_controller.login(login_data, db_session)
```

### Creating a Membership
```python
from pydotorg.domains.users import MembershipService, MembershipCreate, MembershipType

membership_data = MembershipCreate(
    user_id=user.id,
    membership_type=MembershipType.SUPPORTING,
    creator=True,
    psf_member=True
)

membership = await membership_service.create_for_user(
    user_id=user.id,
    data=membership_data.model_dump()
)
```

### Managing User Groups
```python
from pydotorg.domains.users import UserGroupService, UserGroupCreate, UserGroupType

group_data = UserGroupCreate(
    name="Python Web Developers",
    group_type=UserGroupType.USER_GROUP,
    email="webdev@pythonusers.org",
    description="A community for Python web developers"
)

group = await user_group_service.create(group_data.model_dump())

# Approve the group
approved_group = await user_group_service.approve(group.id)

# Mark as trusted
trusted_group = await user_group_service.mark_trusted(group.id)
```

## Architecture

This domain follows the applet template structure:

```
users/
├── __init__.py           # Public API exports
├── urls.py              # URL path constants
├── controllers.py       # Litestar controllers (UserController, MembershipController, UserGroupController)
├── auth_controller.py   # Authentication controller
├── dependencies.py      # DI providers for services and repositories
├── services.py         # Business logic layer
├── models.py           # SQLAlchemy models
├── schemas.py          # Pydantic schemas for validation
├── repositories.py     # Data access layer
├── security.py         # Security utilities
└── README.md          # This file
```

## Dependencies

The domain uses dependency injection for clean separation of concerns:

```python
from pydotorg.domains.users import get_user_dependencies

# Returns dictionary with all DI providers:
# - user_repository / user_service
# - membership_repository / membership_service
# - user_group_repository / user_group_service
```

## Security

- Passwords are hashed using bcrypt via the password_service
- JWT tokens are used for authentication (access + refresh tokens)
- Email privacy settings control visibility of user emails
- User search visibility controls whether users appear in searches
- Account deactivation provides soft delete functionality
- Role-based permissions via is_staff and is_superuser flags

# E2E Tests for Authentication Forms

Comprehensive Playwright E2E tests for authentication forms in the Litestar-pydotorg project.

## Overview

This test suite provides end-to-end testing for all authentication forms using Playwright, covering:

- **Login Form** (`/auth/login`)
- **Registration Form** (`/auth/register`)
- **Forgot Password Form** (`/auth/forgot-password`)
- **Reset Password Form** (`/auth/reset-password/{token}`)

## Test Coverage

### 1. JSON Submission Tests
- ✅ Verify forms submit as JSON (Content-Type: application/json)
- ✅ Verify request body structure matches expected schemas
- ✅ Test that form data is properly serialized to JSON

### 2. Error/Success Message Tests
- ✅ Test error alerts display for invalid credentials
- ✅ Test error alerts for validation failures (weak password, password mismatch)
- ✅ Test success alerts display correctly
- ✅ Verify alert styling (alert-success, alert-error classes)

### 3. Redirect Tests
- ✅ Test login redirects to home on success
- ✅ Test login uses `?next=` parameter when present
- ✅ Test register redirects to login on success
- ✅ Test reset-password redirects to login on success

### 4. Form Validation Tests
- ✅ Test required field validation
- ✅ Test password mismatch client-side validation
- ✅ Test password strength indicator updates
- ✅ Test email format validation

### 5. Accessibility Tests
- ✅ Verify proper labels and ARIA attributes
- ✅ Test error messages are visible and properly styled
- ✅ Test success messages are visible and properly styled

## Setup

### Install Dependencies

```bash
# Install all dependencies including Playwright
uv sync --group dev

# Install Playwright browsers
uv run playwright install chromium
```

### Database Setup

The tests use `pytest-databases` with PostgreSQL in Docker containers. The database is automatically set up and torn down for each test session.

## Running Tests

### Run All E2E Tests

```bash
# Run all E2E tests
uv run pytest tests/e2e/ -v

# Run with specific marker
uv run pytest -m e2e -v
```

### Run Specific Test Classes

```bash
# Run only login form tests
uv run pytest tests/e2e/test_auth_forms.py::TestLoginForm -v

# Run only register form tests
uv run pytest tests/e2e/test_auth_forms.py::TestRegisterForm -v

# Run only forgot password tests
uv run pytest tests/e2e/test_auth_forms.py::TestForgotPasswordForm -v

# Run only reset password tests
uv run pytest tests/e2e/test_auth_forms.py::TestResetPasswordForm -v

# Run accessibility tests
uv run pytest tests/e2e/test_auth_forms.py::TestAuthFormsAccessibility -v
```

### Run Specific Tests

```bash
# Run a single test
uv run pytest tests/e2e/test_auth_forms.py::TestLoginForm::test_login_form_json_submission -v
```

### Run with Coverage

```bash
uv run pytest tests/e2e/ --cov=pydotorg.domains.users --cov-report=html
```

## Test Structure

```
tests/e2e/
├── __init__.py
├── README.md                    # This file
├── conftest.py                  # Playwright fixtures and test app setup
└── test_auth_forms.py          # Comprehensive auth form tests
    ├── TestLoginForm            # Login form tests (8 tests)
    ├── TestRegisterForm         # Registration form tests (10 tests)
    ├── TestForgotPasswordForm   # Forgot password tests (6 tests)
    ├── TestResetPasswordForm    # Reset password tests (10 tests)
    └── TestAuthFormsAccessibility # Accessibility tests (4 tests)
```

## Test Details

### TestLoginForm (8 tests)
- `test_login_form_json_submission` - Verifies JSON submission with correct headers
- `test_login_success_shows_alert_and_redirects` - Success flow validation
- `test_login_with_next_parameter_redirects_correctly` - Next URL parameter handling
- `test_login_invalid_credentials_shows_error` - Error handling for bad credentials
- `test_login_empty_fields_validation` - Required field validation
- `test_login_remember_me_checkbox` - Remember me functionality
- `test_login_spinner_shows_during_submission` - Loading state display

### TestRegisterForm (10 tests)
- `test_register_form_json_submission` - Verifies JSON submission
- `test_register_success_shows_alert_and_redirects` - Success flow
- `test_register_password_mismatch_shows_error` - Password mismatch validation
- `test_register_duplicate_username_shows_error` - Duplicate username handling
- `test_register_duplicate_email_shows_error` - Duplicate email handling
- `test_register_password_strength_indicator` - Password strength UI
- `test_register_required_fields_validation` - Field validation
- `test_register_spinner_shows_during_submission` - Loading state

### TestForgotPasswordForm (6 tests)
- `test_forgot_password_form_json_submission` - JSON submission
- `test_forgot_password_success_shows_message` - Success message display
- `test_forgot_password_nonexistent_email` - Non-existent email handling
- `test_forgot_password_invalid_email_format` - Email format validation
- `test_forgot_password_clears_form_on_success` - Form reset after success
- `test_forgot_password_spinner_shows_during_submission` - Loading state

### TestResetPasswordForm (10 tests)
- `test_reset_password_form_json_submission` - JSON submission with token
- `test_reset_password_token_in_data_attribute` - Token attribute verification
- `test_reset_password_success_redirects_to_login` - Success redirect
- `test_reset_password_mismatch_shows_error` - Password mismatch
- `test_reset_password_weak_password_shows_error` - Weak password validation
- `test_reset_password_invalid_token_shows_error` - Invalid token handling
- `test_reset_password_strength_indicator` - Password strength UI
- `test_reset_password_required_fields_validation` - Field validation
- `test_reset_password_spinner_shows_during_submission` - Loading state

### TestAuthFormsAccessibility (4 tests)
- `test_login_form_labels_and_aria` - Login form accessibility
- `test_register_form_labels_and_aria` - Register form accessibility
- `test_error_messages_are_visible_and_styled` - Error message visibility
- `test_success_messages_are_visible_and_styled` - Success message visibility

## Fixtures

### Playwright Fixtures (from conftest.py)
- `playwright_instance` - Session-scoped Playwright instance
- `browser` - Session-scoped Chromium browser
- `context` - Test-scoped browser context with viewport configuration
- `page` - Test-scoped page instance

### Application Fixtures
- `test_app` - Litestar application with database setup
- `test_server_url` - Base URL for the test server
- `registered_test_user` - Pre-registered test user for login tests

## Configuration

### Playwright Configuration
The tests use:
- **Browser**: Chromium (headless mode)
- **Viewport**: 1280x720
- **Locale**: en-US

### Pytest Configuration
Markers used:
- `@pytest.mark.e2e` - Marks tests as end-to-end tests
- `@pytest.mark.asyncio` - Marks async test functions

## Debugging

### Run in Headed Mode
To see the browser while tests run, modify `conftest.py`:
```python
browser = await playwright_instance.chromium.launch(headless=False)
```

### Slow Down Tests
Add `slow_mo` parameter:
```python
browser = await playwright_instance.chromium.launch(headless=False, slow_mo=1000)
```

### Screenshots on Failure
Playwright automatically captures screenshots on test failures.

### Debug with Playwright Inspector
```bash
PWDEBUG=1 uv run pytest tests/e2e/test_auth_forms.py::TestLoginForm -v
```

## CI/CD Integration

These tests are designed to run in CI/CD pipelines. Ensure:
1. PostgreSQL container is available
2. Playwright browsers are installed: `playwright install chromium`
3. Tests run with `make ci` before committing

## Known Issues and Limitations

1. **Test Server**: Tests currently expect server to be running. Future improvements could auto-start the server.
2. **Email Verification**: Forgot/reset password tests don't verify actual email delivery (uses mocked service).
3. **OAuth**: GitHub OAuth tests are not included (require external service mocking).

## Contributing

When adding new E2E tests:
1. Follow existing test structure and naming conventions
2. Use descriptive test names that explain what is being tested
3. Include docstrings for each test
4. Test both positive and negative scenarios
5. Verify error messages and success messages
6. Test form validation (client-side and server-side)
7. Add appropriate markers (`@pytest.mark.e2e`)

## Maintenance

- **Regular Updates**: Keep Playwright version updated for latest browser support
- **Test Review**: Review tests when UI changes occur
- **Performance**: Monitor test execution time and optimize slow tests
- **Coverage**: Maintain >90% coverage for auth form functionality

"""Playwright E2E tests for authentication forms.

Tests cover:
1. JSON submission - verify forms submit as JSON with correct Content-Type
2. Error/Success messages - test alert displays for different scenarios
3. Redirects - test navigation after successful operations
4. Form validation - client-side validation checks
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from playwright.async_api import Page


@pytest.mark.e2e
class TestLoginForm:
    """E2E tests for the login form."""

    async def test_login_form_json_submission(self, page: Page, test_server_url: str) -> None:
        """Test that login form submits data as JSON with correct Content-Type."""
        await page.goto(f"{test_server_url}/auth/login")

        request_promise = page.wait_for_request(
            lambda req: "/api/auth/session/login" in req.url and req.method == "POST"
        )

        await page.fill('input[name="username"]', "testuser")
        await page.fill('input[name="password"]', "TestPassword123")
        await page.click('button[type="submit"]')

        request = await request_promise

        assert request.headers.get("content-type") == "application/json"

        post_data = request.post_data_json
        assert post_data["username"] == "testuser"
        assert post_data["password"] == "TestPassword123"
        assert isinstance(post_data["remember_me"], bool)

    async def test_login_success_shows_alert_and_redirects(
        self, page: Page, test_server_url: str, registered_test_user: dict
    ) -> None:
        """Test successful login shows success alert and redirects to home."""
        await page.goto(f"{test_server_url}/auth/login")

        await page.fill('input[name="username"]', registered_test_user["username"])
        await page.fill('input[name="password"]', registered_test_user["password"])

        await page.click('button[type="submit"]')

        success_alert = page.locator("#auth-messages .alert-success")
        await success_alert.wait_for(state="visible", timeout=5000)

        assert await success_alert.is_visible()
        success_text = await success_alert.inner_text()
        assert "success" in success_text.lower() or "login" in success_text.lower()

        await page.wait_for_url(f"{test_server_url}/", timeout=5000)
        assert page.url == f"{test_server_url}/"

    async def test_login_with_next_parameter_redirects_correctly(
        self, page: Page, test_server_url: str, registered_test_user: dict
    ) -> None:
        """Test login redirects to ?next= parameter URL on success."""
        next_url = "/auth/profile"
        await page.goto(f"{test_server_url}/auth/login?next={next_url}")

        await page.fill('input[name="username"]', registered_test_user["username"])
        await page.fill('input[name="password"]', registered_test_user["password"])
        await page.click('button[type="submit"]')

        await page.wait_for_url(f"{test_server_url}{next_url}", timeout=5000)
        assert next_url in page.url

    async def test_login_invalid_credentials_shows_error(self, page: Page, test_server_url: str) -> None:
        """Test login with invalid credentials shows error alert."""
        await page.goto(f"{test_server_url}/auth/login")

        await page.fill('input[name="username"]', "nonexistent_user")
        await page.fill('input[name="password"]', "WrongPassword123")
        await page.click('button[type="submit"]')

        error_alert = page.locator("#auth-messages .alert-error")
        await error_alert.wait_for(state="visible", timeout=5000)

        assert await error_alert.is_visible()
        error_text = await error_alert.inner_text()
        assert "invalid" in error_text.lower() or "credentials" in error_text.lower()

    async def test_login_empty_fields_validation(self, page: Page, test_server_url: str) -> None:
        """Test login form validates required fields."""
        await page.goto(f"{test_server_url}/auth/login")

        submit_btn = page.locator('button[type="submit"]')
        await submit_btn.click()

        username_input = page.locator('input[name="username"]')
        password_input = page.locator('input[name="password"]')

        username_validity = await username_input.evaluate("el => el.validity.valid")
        password_validity = await password_input.evaluate("el => el.validity.valid")

        assert not username_validity, "Username should be invalid when empty"
        assert not password_validity, "Password should be invalid when empty"

    async def test_login_remember_me_checkbox(self, page: Page, test_server_url: str) -> None:
        """Test remember_me checkbox is included in form submission."""
        await page.goto(f"{test_server_url}/auth/login")

        request_promise = page.wait_for_request(
            lambda req: "/api/auth/session/login" in req.url and req.method == "POST"
        )

        await page.fill('input[name="username"]', "testuser")
        await page.fill('input[name="password"]', "TestPassword123")
        await page.check('input[name="remember_me"]')
        await page.click('button[type="submit"]')

        request = await request_promise
        post_data = request.post_data_json

        assert post_data["remember_me"] is True

    async def test_login_spinner_shows_during_submission(self, page: Page, test_server_url: str) -> None:
        """Test loading spinner displays during form submission."""
        await page.goto(f"{test_server_url}/auth/login")

        await page.fill('input[name="username"]', "testuser")
        await page.fill('input[name="password"]', "TestPassword123")

        spinner = page.locator("#login-spinner")

        initial_class = await spinner.get_attribute("class")
        assert "htmx-indicator" in initial_class, "Spinner should be hidden initially"

        submit_promise = page.click('button[type="submit"]')

        await page.wait_for_function(
            """() => {
                const spinner = document.getElementById('login-spinner');
                return !spinner.classList.contains('htmx-indicator');
            }""",
            timeout=2000,
        )

        await submit_promise


@pytest.mark.e2e
class TestRegisterForm:
    """E2E tests for the registration form."""

    async def test_register_form_json_submission(self, page: Page, test_server_url: str) -> None:
        """Test that register form submits data as JSON with correct Content-Type."""
        await page.goto(f"{test_server_url}/auth/register")

        request_promise = page.wait_for_request(lambda req: "/api/auth/register" in req.url and req.method == "POST")

        await page.fill('input[name="first_name"]', "John")
        await page.fill('input[name="last_name"]', "Doe")
        await page.fill('input[name="username"]', "johndoe")
        await page.fill('input[name="email"]', "john@example.com")
        await page.fill('input[name="password"]', "StrongPass123!")
        await page.fill('input[name="password_confirm"]', "StrongPass123!")
        await page.click('button[type="submit"]')

        request = await request_promise

        assert request.headers.get("content-type") == "application/json"

        post_data = request.post_data_json
        assert post_data["first_name"] == "John"
        assert post_data["last_name"] == "Doe"
        assert post_data["username"] == "johndoe"
        assert post_data["email"] == "john@example.com"
        assert post_data["password"] == "StrongPass123!"
        assert post_data["password_confirm"] == "StrongPass123!"

    async def test_register_success_shows_alert_and_redirects(self, page: Page, test_server_url: str) -> None:
        """Test successful registration shows success alert and redirects to login."""
        await page.goto(f"{test_server_url}/auth/register")

        await page.fill('input[name="first_name"]', "Jane")
        await page.fill('input[name="last_name"]', "Smith")
        await page.fill('input[name="username"]', "janesmith")
        await page.fill('input[name="email"]', "jane@example.com")
        await page.fill('input[name="password"]', "SecurePass123!")
        await page.fill('input[name="password_confirm"]', "SecurePass123!")

        await page.click('button[type="submit"]')

        success_alert = page.locator("#register-messages .alert-success")
        await success_alert.wait_for(state="visible", timeout=5000)

        assert await success_alert.is_visible()
        success_text = await success_alert.inner_text()
        assert "success" in success_text.lower() or "account" in success_text.lower()

        await page.wait_for_url(f"{test_server_url}/auth/login", timeout=5000)
        assert "/auth/login" in page.url

    async def test_register_password_mismatch_shows_error(self, page: Page, test_server_url: str) -> None:
        """Test registration with mismatched passwords shows client-side error."""
        await page.goto(f"{test_server_url}/auth/register")

        await page.fill('input[name="first_name"]', "Test")
        await page.fill('input[name="last_name"]', "User")
        await page.fill('input[name="username"]', "testuser123")
        await page.fill('input[name="email"]', "test@example.com")
        await page.fill('input[name="password"]', "Password123!")
        await page.fill('input[name="password_confirm"]', "DifferentPass123!")

        await page.click('button[type="submit"]')

        error_alert = page.locator("#register-messages .alert-error")
        await error_alert.wait_for(state="visible", timeout=5000)

        assert await error_alert.is_visible()
        error_text = await error_alert.inner_text()
        assert "password" in error_text.lower() and "match" in error_text.lower()

    async def test_register_duplicate_username_shows_error(
        self, page: Page, test_server_url: str, registered_test_user: dict
    ) -> None:
        """Test registration with existing username shows server error."""
        await page.goto(f"{test_server_url}/auth/register")

        await page.fill('input[name="first_name"]', "Another")
        await page.fill('input[name="last_name"]', "User")
        await page.fill('input[name="username"]', registered_test_user["username"])
        await page.fill('input[name="email"]', "different@example.com")
        await page.fill('input[name="password"]', "ValidPass123!")
        await page.fill('input[name="password_confirm"]', "ValidPass123!")

        await page.click('button[type="submit"]')

        error_alert = page.locator("#register-messages .alert-error")
        await error_alert.wait_for(state="visible", timeout=5000)

        assert await error_alert.is_visible()
        error_text = await error_alert.inner_text()
        assert "username" in error_text.lower() or "already" in error_text.lower()

    async def test_register_duplicate_email_shows_error(
        self, page: Page, test_server_url: str, registered_test_user: dict
    ) -> None:
        """Test registration with existing email shows server error."""
        await page.goto(f"{test_server_url}/auth/register")

        await page.fill('input[name="first_name"]', "Another")
        await page.fill('input[name="last_name"]', "User")
        await page.fill('input[name="username"]', "uniqueusername123")
        await page.fill('input[name="email"]', registered_test_user["email"])
        await page.fill('input[name="password"]', "ValidPass123!")
        await page.fill('input[name="password_confirm"]', "ValidPass123!")

        await page.click('button[type="submit"]')

        error_alert = page.locator("#register-messages .alert-error")
        await error_alert.wait_for(state="visible", timeout=5000)

        assert await error_alert.is_visible()
        error_text = await error_alert.inner_text()
        assert "email" in error_text.lower() or "registered" in error_text.lower()

    async def test_register_password_strength_indicator(self, page: Page, test_server_url: str) -> None:
        """Test password strength indicator updates as user types."""
        await page.goto(f"{test_server_url}/auth/register")

        password_input = page.locator('input[name="password"]')

        await password_input.fill("weak")
        await page.wait_for_timeout(300)

        strength_text = page.locator("text=Weak password")
        assert await strength_text.is_visible()

        await password_input.fill("StrongPassword123!")
        await page.wait_for_timeout(300)

        strong_text = page.locator("text=Strong password")
        assert await strong_text.is_visible()

    async def test_register_required_fields_validation(self, page: Page, test_server_url: str) -> None:
        """Test all required fields are validated."""
        await page.goto(f"{test_server_url}/auth/register")

        submit_btn = page.locator('button[type="submit"]')
        await submit_btn.click()

        required_fields = [
            'input[name="first_name"]',
            'input[name="last_name"]',
            'input[name="username"]',
            'input[name="email"]',
            'input[name="password"]',
            'input[name="password_confirm"]',
        ]

        for field_selector in required_fields:
            field = page.locator(field_selector)
            validity = await field.evaluate("el => el.validity.valid")
            assert not validity, f"Field {field_selector} should be invalid when empty"

    async def test_register_spinner_shows_during_submission(self, page: Page, test_server_url: str) -> None:
        """Test loading spinner displays during form submission."""
        await page.goto(f"{test_server_url}/auth/register")

        await page.fill('input[name="first_name"]', "Test")
        await page.fill('input[name="last_name"]', "User")
        await page.fill('input[name="username"]', "testspinner")
        await page.fill('input[name="email"]', "spinner@test.com")
        await page.fill('input[name="password"]', "TestPass123!")
        await page.fill('input[name="password_confirm"]', "TestPass123!")

        spinner = page.locator("#register-spinner")

        initial_class = await spinner.get_attribute("class")
        assert "htmx-indicator" in initial_class, "Spinner should be hidden initially"

        submit_promise = page.click('button[type="submit"]')

        await page.wait_for_function(
            """() => {
                const spinner = document.getElementById('register-spinner');
                return !spinner.classList.contains('htmx-indicator');
            }""",
            timeout=2000,
        )

        await submit_promise


@pytest.mark.e2e
class TestForgotPasswordForm:
    """E2E tests for the forgot password form."""

    async def test_forgot_password_form_json_submission(self, page: Page, test_server_url: str) -> None:
        """Test that forgot password form submits data as JSON with correct Content-Type."""
        await page.goto(f"{test_server_url}/auth/forgot-password")

        request_promise = page.wait_for_request(
            lambda req: "/api/auth/forgot-password" in req.url and req.method == "POST"
        )

        await page.fill('input[name="email"]', "test@example.com")
        await page.click('button[type="submit"]')

        request = await request_promise

        assert request.headers.get("content-type") == "application/json"

        post_data = request.post_data_json
        assert post_data["email"] == "test@example.com"

    async def test_forgot_password_success_shows_message(
        self, page: Page, test_server_url: str, registered_test_user: dict
    ) -> None:
        """Test successful forgot password request shows success message."""
        await page.goto(f"{test_server_url}/auth/forgot-password")

        await page.fill('input[name="email"]', registered_test_user["email"])
        await page.click('button[type="submit"]')

        success_alert = page.locator("#forgot-messages .alert-success")
        await success_alert.wait_for(state="visible", timeout=5000)

        assert await success_alert.is_visible()
        success_text = await success_alert.inner_text()
        assert "reset" in success_text.lower() or "email" in success_text.lower()

    async def test_forgot_password_nonexistent_email(self, page: Page, test_server_url: str) -> None:
        """Test forgot password with non-existent email shows error."""
        await page.goto(f"{test_server_url}/auth/forgot-password")

        await page.fill('input[name="email"]', "nonexistent@example.com")
        await page.click('button[type="submit"]')

        error_alert = page.locator("#forgot-messages .alert-error")
        await error_alert.wait_for(state="visible", timeout=5000)

        assert await error_alert.is_visible()

    async def test_forgot_password_invalid_email_format(self, page: Page, test_server_url: str) -> None:
        """Test forgot password validates email format."""
        await page.goto(f"{test_server_url}/auth/forgot-password")

        email_input = page.locator('input[name="email"]')
        await email_input.fill("invalid-email-format")

        validity = await email_input.evaluate("el => el.validity.valid")
        assert not validity, "Email field should be invalid with incorrect format"

    async def test_forgot_password_clears_form_on_success(
        self, page: Page, test_server_url: str, registered_test_user: dict
    ) -> None:
        """Test form is cleared after successful submission."""
        await page.goto(f"{test_server_url}/auth/forgot-password")

        await page.fill('input[name="email"]', registered_test_user["email"])
        await page.click('button[type="submit"]')

        success_alert = page.locator("#forgot-messages .alert-success")
        await success_alert.wait_for(state="visible", timeout=5000)

        email_value = await page.locator('input[name="email"]').input_value()
        assert email_value == "", "Email field should be cleared after success"

    async def test_forgot_password_spinner_shows_during_submission(self, page: Page, test_server_url: str) -> None:
        """Test loading spinner displays during form submission."""
        await page.goto(f"{test_server_url}/auth/forgot-password")

        await page.fill('input[name="email"]', "test@example.com")

        spinner = page.locator("#forgot-spinner")

        initial_class = await spinner.get_attribute("class")
        assert "htmx-indicator" in initial_class, "Spinner should be hidden initially"

        submit_promise = page.click('button[type="submit"]')

        await page.wait_for_function(
            """() => {
                const spinner = document.getElementById('forgot-spinner');
                return !spinner.classList.contains('htmx-indicator');
            }""",
            timeout=2000,
        )

        await submit_promise


@pytest.mark.e2e
class TestResetPasswordForm:
    """E2E tests for the reset password form."""

    async def test_reset_password_form_json_submission(self, page: Page, test_server_url: str) -> None:
        """Test that reset password form submits data as JSON with correct Content-Type."""
        test_token = "test_reset_token_12345"
        await page.goto(f"{test_server_url}/auth/reset-password/{test_token}")

        request_promise = page.wait_for_request(
            lambda req: "/api/auth/reset-password" in req.url and req.method == "POST"
        )

        await page.fill('input[name="new_password"]', "NewPassword123!")
        await page.fill('input[name="confirm_password"]', "NewPassword123!")
        await page.click('button[type="submit"]')

        request = await request_promise

        assert request.headers.get("content-type") == "application/json"

        post_data = request.post_data_json
        assert post_data["token"] == test_token
        assert post_data["new_password"] == "NewPassword123!"
        assert post_data["confirm_password"] == "NewPassword123!"

    async def test_reset_password_token_in_data_attribute(self, page: Page, test_server_url: str) -> None:
        """Test that token is properly set in form data attribute."""
        test_token = "test_token_abc123"
        await page.goto(f"{test_server_url}/auth/reset-password/{test_token}")

        form = page.locator("#reset-form")
        token_attr = await form.get_attribute("data-token")

        assert token_attr == test_token

    async def test_reset_password_success_redirects_to_login(self, page: Page, test_server_url: str) -> None:
        """Test successful password reset redirects to login page."""
        test_token = "valid_reset_token"
        await page.goto(f"{test_server_url}/auth/reset-password/{test_token}")

        await page.fill('input[name="new_password"]', "NewSecurePass123!")
        await page.fill('input[name="confirm_password"]', "NewSecurePass123!")

        await page.click('button[type="submit"]')

        success_alert = page.locator("#reset-messages .alert-success")
        await success_alert.wait_for(state="visible", timeout=5000)

        await page.wait_for_url(f"{test_server_url}/auth/login", timeout=5000)
        assert "/auth/login" in page.url

    async def test_reset_password_mismatch_shows_error(self, page: Page, test_server_url: str) -> None:
        """Test password mismatch shows client-side error."""
        test_token = "test_token"
        await page.goto(f"{test_server_url}/auth/reset-password/{test_token}")

        await page.fill('input[name="new_password"]', "Password123!")
        await page.fill('input[name="confirm_password"]', "DifferentPass123!")

        await page.click('button[type="submit"]')

        error_alert = page.locator("#reset-messages .alert-error")
        await error_alert.wait_for(state="visible", timeout=5000)

        assert await error_alert.is_visible()
        error_text = await error_alert.inner_text()
        assert "password" in error_text.lower() and "match" in error_text.lower()

    async def test_reset_password_weak_password_shows_error(self, page: Page, test_server_url: str) -> None:
        """Test weak password shows validation error."""
        test_token = "test_token"
        await page.goto(f"{test_server_url}/auth/reset-password/{test_token}")

        await page.fill('input[name="new_password"]', "weak")
        await page.fill('input[name="confirm_password"]', "weak")

        await page.click('button[type="submit"]')

        error_alert = page.locator("#reset-messages .alert-error")
        await error_alert.wait_for(state="visible", timeout=5000)

        assert await error_alert.is_visible()

    async def test_reset_password_invalid_token_shows_error(self, page: Page, test_server_url: str) -> None:
        """Test invalid reset token shows error message."""
        invalid_token = "invalid_expired_token"
        await page.goto(f"{test_server_url}/auth/reset-password/{invalid_token}")

        await page.fill('input[name="new_password"]', "ValidPassword123!")
        await page.fill('input[name="confirm_password"]', "ValidPassword123!")

        await page.click('button[type="submit"]')

        error_alert = page.locator("#reset-messages .alert-error")
        await error_alert.wait_for(state="visible", timeout=5000)

        assert await error_alert.is_visible()

    async def test_reset_password_strength_indicator(self, page: Page, test_server_url: str) -> None:
        """Test password strength indicator updates as user types."""
        test_token = "test_token"
        await page.goto(f"{test_server_url}/auth/reset-password/{test_token}")

        password_input = page.locator('input[name="new_password"]')

        await password_input.fill("weak")
        await page.wait_for_timeout(300)

        strength_text = page.locator("text=Weak password")
        assert await strength_text.is_visible()

        await password_input.fill("VeryStrongPassword123!")
        await page.wait_for_timeout(300)

        strong_text = page.locator("text=Strong password")
        assert await strong_text.is_visible()

    async def test_reset_password_required_fields_validation(self, page: Page, test_server_url: str) -> None:
        """Test required fields are validated."""
        test_token = "test_token"
        await page.goto(f"{test_server_url}/auth/reset-password/{test_token}")

        submit_btn = page.locator('button[type="submit"]')
        await submit_btn.click()

        new_password_field = page.locator('input[name="new_password"]')
        confirm_password_field = page.locator('input[name="confirm_password"]')

        new_password_validity = await new_password_field.evaluate("el => el.validity.valid")
        confirm_password_validity = await confirm_password_field.evaluate("el => el.validity.valid")

        assert not new_password_validity, "New password should be invalid when empty"
        assert not confirm_password_validity, "Confirm password should be invalid when empty"

    async def test_reset_password_spinner_shows_during_submission(self, page: Page, test_server_url: str) -> None:
        """Test loading spinner displays during form submission."""
        test_token = "test_token"
        await page.goto(f"{test_server_url}/auth/reset-password/{test_token}")

        await page.fill('input[name="new_password"]', "NewPassword123!")
        await page.fill('input[name="confirm_password"]', "NewPassword123!")

        spinner = page.locator("#reset-spinner")

        initial_class = await spinner.get_attribute("class")
        assert "htmx-indicator" in initial_class, "Spinner should be hidden initially"

        submit_promise = page.click('button[type="submit"]')

        await page.wait_for_function(
            """() => {
                const spinner = document.getElementById('reset-spinner');
                return !spinner.classList.contains('htmx-indicator');
            }""",
            timeout=2000,
        )

        await submit_promise


@pytest.mark.e2e
class TestAuthFormsAccessibility:
    """E2E tests for accessibility features of auth forms."""

    async def test_login_form_labels_and_aria(self, page: Page, test_server_url: str) -> None:
        """Test login form has proper labels and ARIA attributes."""
        await page.goto(f"{test_server_url}/auth/login")

        username_input = page.locator('input[name="username"]')
        password_input = page.locator('input[name="password"]')

        assert await username_input.get_attribute("required") is not None
        assert await password_input.get_attribute("required") is not None

    async def test_register_form_labels_and_aria(self, page: Page, test_server_url: str) -> None:
        """Test register form has proper labels and ARIA attributes."""
        await page.goto(f"{test_server_url}/auth/register")

        required_inputs = [
            'input[name="first_name"]',
            'input[name="last_name"]',
            'input[name="username"]',
            'input[name="email"]',
            'input[name="password"]',
            'input[name="password_confirm"]',
        ]

        for selector in required_inputs:
            input_field = page.locator(selector)
            assert await input_field.get_attribute("required") is not None

    async def test_error_messages_are_visible_and_styled(self, page: Page, test_server_url: str) -> None:
        """Test error messages have proper styling for visibility."""
        await page.goto(f"{test_server_url}/auth/login")

        await page.fill('input[name="username"]', "invalid")
        await page.fill('input[name="password"]', "invalid")
        await page.click('button[type="submit"]')

        error_alert = page.locator("#auth-messages .alert-error")
        await error_alert.wait_for(state="visible", timeout=5000)

        assert "alert-error" in await error_alert.get_attribute("class")

    async def test_success_messages_are_visible_and_styled(
        self, page: Page, test_server_url: str, registered_test_user: dict
    ) -> None:
        """Test success messages have proper styling for visibility."""
        await page.goto(f"{test_server_url}/auth/login")

        await page.fill('input[name="username"]', registered_test_user["username"])
        await page.fill('input[name="password"]', registered_test_user["password"])
        await page.click('button[type="submit"]')

        success_alert = page.locator("#auth-messages .alert-success")
        await success_alert.wait_for(state="visible", timeout=5000)

        assert "alert-success" in await success_alert.get_attribute("class")

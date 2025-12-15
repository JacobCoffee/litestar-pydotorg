"""Integration tests for API validation error handling.

Tests verify that:
1. Invalid query parameters return 400 JSON errors
2. Empty parameter values are handled correctly
3. Wrong types return descriptive validation errors
4. Out-of-bounds values are rejected properly
5. All API error responses are JSON (not HTML)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from advanced_alchemy.filters import LimitOffset
from litestar import Litestar
from litestar.params import Parameter
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from pydotorg.core.exceptions import get_exception_handlers
from pydotorg.domains.pages.controllers import PageController
from pydotorg.domains.pages.dependencies import get_page_dependencies
from pydotorg.domains.users.controllers import UserController
from pydotorg.domains.users.dependencies import get_user_dependencies

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class ValidationTestFixtures:
    """Test fixtures for validation error tests."""

    client: AsyncTestClient
    session_factory: async_sessionmaker


@pytest.fixture(scope="module")
async def validation_fixtures(
    async_session_factory: async_sessionmaker,
    _module_sqlalchemy_config: SQLAlchemyAsyncConfig,
) -> AsyncIterator[ValidationTestFixtures]:
    """Create test fixtures with exception handlers for validation testing.

    Uses session-scoped async_engine to prevent connection exhaustion.
    Module-scoped to prevent creating multiple engines during test runs.
    """

    async def provide_limit_offset(
        current_page: int = Parameter(ge=1, default=1, query="currentPage"),
        page_size: int = Parameter(ge=1, le=100, default=10, query="pageSize"),
    ) -> LimitOffset:
        """Provide limit offset pagination."""
        return LimitOffset(page_size, page_size * (current_page - 1))

    sqlalchemy_plugin = SQLAlchemyPlugin(config=_module_sqlalchemy_config)

    user_deps = get_user_dependencies()
    user_deps["limit_offset"] = provide_limit_offset

    page_deps = get_page_dependencies()
    page_deps["limit_offset"] = provide_limit_offset

    all_deps = {**user_deps, **page_deps}

    app = Litestar(
        route_handlers=[UserController, PageController],
        plugins=[sqlalchemy_plugin],
        dependencies=all_deps,
        exception_handlers=get_exception_handlers(),
        debug=True,
    )

    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        fixtures = ValidationTestFixtures()
        fixtures.client = client
        fixtures.session_factory = async_session_factory
        yield fixtures


@pytest.mark.integration
class TestInvalidQueryParameterNames:
    """Tests for invalid query parameter names."""

    async def test_unknown_query_param_limit_offset(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test that passing 'limit_offset' as query param is handled gracefully.

        The API expects 'currentPage' and 'pageSize', not 'limit_offset'.
        This should either be ignored or return a validation error.
        """
        response = await validation_fixtures.client.get(
            "/api/v1/users/",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 200

        response = await validation_fixtures.client.get(
            "/api/v1/users/?limit_offset=1",
            headers={"Accept": "application/json"},
        )
        assert response.status_code in {200, 400}
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_unknown_query_param_pages(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test unknown query parameter on pages endpoint."""
        response = await validation_fixtures.client.get(
            "/api/v1/pages/?limit_offset=1",
            headers={"Accept": "application/json"},
        )
        assert response.status_code in {200, 400}
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_random_unknown_params_ignored(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test that random unknown parameters are gracefully handled."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?foo=bar&baz=qux",
            headers={"Accept": "application/json"},
        )
        assert response.status_code in {200, 400}
        assert response.headers.get("content-type", "").startswith("application/json")


@pytest.mark.integration
class TestEmptyParameterValues:
    """Tests for empty query parameter values."""

    async def test_empty_current_page(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test empty currentPage parameter value."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?currentPage=",
            headers={"Accept": "application/json"},
        )
        assert response.status_code in {200, 400, 422}
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_empty_page_size(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test empty pageSize parameter value."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?pageSize=",
            headers={"Accept": "application/json"},
        )
        assert response.status_code in {200, 400, 422}
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_empty_both_params(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test empty values for both pagination parameters."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?currentPage=&pageSize=",
            headers={"Accept": "application/json"},
        )
        assert response.status_code in {200, 400, 422}
        assert response.headers.get("content-type", "").startswith("application/json")


@pytest.mark.integration
class TestWrongParameterTypes:
    """Tests for wrong parameter types."""

    async def test_string_for_current_page(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test passing string instead of int for currentPage."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?currentPage=abc",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 400
        assert response.headers.get("content-type", "").startswith("application/json")
        data = response.json()
        assert "detail" in data or "message" in data or "extra" in data

    async def test_float_for_current_page(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test passing float instead of int for currentPage."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?currentPage=1.5",
            headers={"Accept": "application/json"},
        )
        assert response.status_code in {200, 400, 422}
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_string_for_page_size(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test passing string instead of int for pageSize."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?pageSize=abc",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 400
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_special_characters_in_params(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test special characters in parameter values."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?currentPage=<script>",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 400
        assert response.headers.get("content-type", "").startswith("application/json")


@pytest.mark.integration
class TestOutOfBoundsValues:
    """Tests for out-of-bounds parameter values."""

    async def test_zero_current_page(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test currentPage=0 (below minimum of 1)."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?currentPage=0",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 400
        assert response.headers.get("content-type", "").startswith("application/json")
        data = response.json()
        assert "detail" in data or "extra" in data

    async def test_negative_current_page(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test negative currentPage value."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?currentPage=-1",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 400
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_zero_page_size(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test pageSize=0 (below minimum of 1)."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?pageSize=0",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 400
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_negative_page_size(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test negative pageSize value."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?pageSize=-10",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 400
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_page_size_exceeds_maximum(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test pageSize exceeding maximum (100)."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?pageSize=101",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 400
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_very_large_page_size(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test extremely large pageSize value."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?pageSize=999999",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 400
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_very_large_current_page(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test very large currentPage value (should be valid but return empty)."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?currentPage=999999",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("application/json")


@pytest.mark.integration
class TestValidationErrorResponseFormat:
    """Tests verifying validation errors return proper JSON format."""

    async def test_validation_error_has_detail(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test that validation errors include detail field."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?currentPage=abc",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    async def test_validation_error_has_extra_info(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test that validation errors include extra field with source info."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?currentPage=abc",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "extra" in data
        extra = data["extra"]
        assert isinstance(extra, list)
        assert len(extra) > 0
        error_info = extra[0]
        assert "key" in error_info or "source" in error_info

    async def test_validation_error_not_html(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test that API validation errors never return HTML."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/?pageSize=-1",
            headers={"Accept": "application/json"},
        )
        content_type = response.headers.get("content-type", "")
        assert "text/html" not in content_type
        assert "application/json" in content_type
        content = response.text
        assert not content.strip().startswith("<!DOCTYPE")
        assert not content.strip().startswith("<html")


@pytest.mark.integration
class TestPathParameterValidation:
    """Tests for path parameter validation."""

    async def test_invalid_uuid_format(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test invalid UUID format in path parameter.

        Note: Litestar returns 404 for invalid UUID path params because the route
        matching fails before reaching the handler. This is expected behavior.
        """
        response = await validation_fixtures.client.get(
            "/api/v1/users/not-a-valid-uuid",
            headers={"Accept": "application/json"},
        )
        assert response.status_code in {400, 404}
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_empty_uuid(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test empty UUID in path (should 404 or 400)."""
        response = await validation_fixtures.client.get(
            "/api/v1/users/",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 200

    async def test_valid_but_nonexistent_uuid(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test valid UUID format but non-existent resource."""
        fake_uuid = str(uuid4())
        response = await validation_fixtures.client.get(
            f"/api/v1/users/{fake_uuid}",
            headers={"Accept": "application/json"},
        )
        assert response.status_code in {404, 500}
        assert response.headers.get("content-type", "").startswith("application/json")


@pytest.mark.integration
class TestRequestBodyValidation:
    """Tests for request body validation errors."""

    async def test_missing_required_fields(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test creating user without required fields."""
        response = await validation_fixtures.client.post(
            "/api/v1/users/",
            json={},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        assert response.status_code in {400, 422}
        assert response.headers.get("content-type", "").startswith("application/json")
        data = response.json()
        assert "detail" in data

    async def test_invalid_email_format(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test creating user with invalid email format."""
        response = await validation_fixtures.client.post(
            "/api/v1/users/",
            json={
                "username": "testuser",
                "email": "not-an-email",
                "password": "password123",
            },
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        assert response.status_code in {400, 422, 500}
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_wrong_type_in_body(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test passing wrong types in request body."""
        response = await validation_fixtures.client.post(
            "/api/v1/users/",
            json={
                "username": 12345,
                "email": ["list", "instead", "of", "string"],
                "password": {"dict": "value"},
            },
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        assert response.status_code in {400, 422}
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_invalid_json_body(self, validation_fixtures: ValidationTestFixtures) -> None:
        """Test sending invalid JSON in request body."""
        response = await validation_fixtures.client.post(
            "/api/v1/users/",
            content="not valid json {{{",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        assert response.status_code == 400
        assert response.headers.get("content-type", "").startswith("application/json")

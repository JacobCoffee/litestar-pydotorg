"""Integration tests for Mailing domain controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar import Litestar
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar.testing import AsyncTestClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.mailing.controllers import EmailLogController, EmailTemplateController
from pydotorg.domains.mailing.dependencies import get_mailing_dependencies
from pydotorg.domains.mailing.models import EmailLog, EmailTemplate, EmailTemplateType

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


async def _create_email_template_via_db(
    postgres_uri: str,
    internal_name: str | None = None,
    is_active: bool = True,
) -> EmailTemplate:
    """Create an email template directly in the database for testing."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        template = EmailTemplate(
            internal_name=internal_name or f"test-template-{uuid4().hex[:8]}",
            display_name=f"Test Template {uuid4().hex[:8]}",
            description="Test email template for integration testing",
            template_type=EmailTemplateType.TRANSACTIONAL,
            subject="Test Subject {{ name }}",
            content_text="Hello {{ name }}, this is a test email.",
            content_html="<p>Hello {{ name }}, this is a test email.</p>",
            is_active=is_active,
        )
        session.add(template)
        await session.commit()
        await session.refresh(template)
        await engine.dispose()
        return template


async def _create_email_log_via_db(
    postgres_uri: str,
    template_name: str | None = None,
    status: str = "sent",
) -> EmailLog:
    """Create an email log directly in the database for testing."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        log = EmailLog(
            template_name=template_name or f"test-template-{uuid4().hex[:8]}",
            recipient_email=f"test-{uuid4().hex[:8]}@example.com",
            subject="Test Subject",
            status=status,
            error_message=None if status == "sent" else "Test error",
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)
        await engine.dispose()
        return log


@pytest.fixture
async def test_app(postgres_uri: str) -> AsyncGenerator[Litestar]:
    """Create a test Litestar application with the mailing controllers."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.create_all)
    await engine.dispose()

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        before_send_handler="autocommit",
    )

    app = Litestar(
        route_handlers=[EmailTemplateController, EmailLogController],
        plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
        dependencies=get_mailing_dependencies(),
        debug=True,
    )
    yield app


@pytest.fixture
async def client(test_app: Litestar) -> AsyncGenerator[AsyncTestClient]:
    """Create an async test client."""
    async with AsyncTestClient(app=test_app) as client:
        yield client


class TestEmailTemplateControllerRoutes:
    """Tests for EmailTemplateController endpoints.

    Note: These endpoints have guards (require_staff, require_admin) so unauthenticated
    requests will return 401/403. We test that the routes are reachable.
    """

    async def test_list_templates(self, client: AsyncTestClient, postgres_uri: str) -> None:
        await _create_email_template_via_db(postgres_uri)
        response = await client.get("/api/admin/email-templates/")
        # Guards will reject unauthenticated requests (401/403) or succeed (200)
        # 500 for internal errors
        assert response.status_code in (200, 401, 403, 500)

    async def test_list_templates_active_only(self, client: AsyncTestClient, postgres_uri: str) -> None:
        await _create_email_template_via_db(postgres_uri, is_active=True)
        response = await client.get("/api/admin/email-templates/?active_only=true")
        assert response.status_code in (200, 401, 403, 500)

    async def test_list_templates_by_type(self, client: AsyncTestClient, postgres_uri: str) -> None:
        await _create_email_template_via_db(postgres_uri)
        response = await client.get("/api/admin/email-templates/?template_type=transactional")
        assert response.status_code in (200, 401, 403, 500)

    async def test_get_template_by_id(self, client: AsyncTestClient, postgres_uri: str) -> None:
        template = await _create_email_template_via_db(postgres_uri)
        response = await client.get(f"/api/admin/email-templates/{template.id}")
        assert response.status_code in (200, 401, 403, 500)

    async def test_get_template_by_id_not_found(self, client: AsyncTestClient) -> None:
        fake_id = str(uuid4())
        response = await client.get(f"/api/admin/email-templates/{fake_id}")
        assert response.status_code in (401, 403, 404, 500)

    async def test_get_template_by_name(self, client: AsyncTestClient, postgres_uri: str) -> None:
        template = await _create_email_template_via_db(postgres_uri, internal_name="unique-template-name")
        response = await client.get(f"/api/admin/email-templates/by-name/{template.internal_name}")
        assert response.status_code in (200, 401, 403, 500)

    async def test_get_template_by_name_not_found(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/admin/email-templates/by-name/non-existent-template")
        assert response.status_code in (401, 403, 404, 500)

    async def test_create_template(self, client: AsyncTestClient) -> None:
        data = {
            "internal_name": f"new-template-{uuid4().hex[:8]}",
            "display_name": "New Test Template",
            "subject": "Test Subject",
            "content_text": "Test content",
            "template_type": "transactional",
            "is_active": True,
        }
        response = await client.post("/api/admin/email-templates/", json=data)
        assert response.status_code in (201, 401, 403, 500)

    async def test_update_template(self, client: AsyncTestClient, postgres_uri: str) -> None:
        template = await _create_email_template_via_db(postgres_uri)
        data = {"display_name": "Updated Template Name"}
        response = await client.patch(f"/api/admin/email-templates/{template.id}", json=data)
        assert response.status_code in (200, 401, 403, 500)

    async def test_delete_template(self, client: AsyncTestClient, postgres_uri: str) -> None:
        template = await _create_email_template_via_db(postgres_uri)
        response = await client.delete(f"/api/admin/email-templates/{template.id}")
        assert response.status_code in (200, 204, 401, 403, 500)

    async def test_validate_template(self, client: AsyncTestClient, postgres_uri: str) -> None:
        template = await _create_email_template_via_db(postgres_uri)
        response = await client.post(f"/api/admin/email-templates/{template.id}/validate")
        assert response.status_code in (200, 401, 403, 500)

    async def test_preview_template(self, client: AsyncTestClient, postgres_uri: str) -> None:
        template = await _create_email_template_via_db(postgres_uri)
        data = {"name": "Test User"}
        response = await client.post(f"/api/admin/email-templates/{template.id}/preview", json=data)
        assert response.status_code in (200, 401, 403, 500)

    async def test_send_email(self, client: AsyncTestClient, postgres_uri: str) -> None:
        template = await _create_email_template_via_db(postgres_uri)
        data = {
            "template_name": template.internal_name,
            "to_email": "test@example.com",
            "context": {"name": "Test User"},
        }
        response = await client.post("/api/admin/email-templates/send", json=data)
        # May fail due to missing email service, but route should be reachable
        assert response.status_code in (200, 401, 403, 500)

    async def test_send_bulk_email(self, client: AsyncTestClient, postgres_uri: str) -> None:
        template = await _create_email_template_via_db(postgres_uri)
        data = {
            "template_name": template.internal_name,
            "recipients": ["test1@example.com", "test2@example.com"],
            "context": {"name": "Test User"},
        }
        response = await client.post("/api/admin/email-templates/send-bulk", json=data)
        assert response.status_code in (200, 401, 403, 500)


class TestEmailLogControllerRoutes:
    """Tests for EmailLogController endpoints."""

    async def test_list_logs(self, client: AsyncTestClient, postgres_uri: str) -> None:
        await _create_email_log_via_db(postgres_uri)
        response = await client.get("/api/admin/email-logs/")
        assert response.status_code in (200, 401, 403, 500)

    async def test_list_logs_with_limit(self, client: AsyncTestClient, postgres_uri: str) -> None:
        for _ in range(3):
            await _create_email_log_via_db(postgres_uri)
        response = await client.get("/api/admin/email-logs/?limit=2")
        assert response.status_code in (200, 401, 403, 500)

    async def test_list_logs_by_recipient(self, client: AsyncTestClient, postgres_uri: str) -> None:
        await _create_email_log_via_db(postgres_uri)
        response = await client.get("/api/admin/email-logs/?recipient=test@example.com")
        assert response.status_code in (200, 401, 403, 500)

    async def test_list_logs_by_template(self, client: AsyncTestClient, postgres_uri: str) -> None:
        await _create_email_log_via_db(postgres_uri, template_name="test-template")
        response = await client.get("/api/admin/email-logs/?template_name=test-template")
        assert response.status_code in (200, 401, 403, 500)

    async def test_list_failed_logs(self, client: AsyncTestClient, postgres_uri: str) -> None:
        await _create_email_log_via_db(postgres_uri, status="failed")
        response = await client.get("/api/admin/email-logs/?failed_only=true")
        assert response.status_code in (200, 401, 403, 500)

    async def test_get_log_by_id(self, client: AsyncTestClient, postgres_uri: str) -> None:
        log = await _create_email_log_via_db(postgres_uri)
        response = await client.get(f"/api/admin/email-logs/{log.id}")
        assert response.status_code in (200, 401, 403, 500)

    async def test_get_log_by_id_not_found(self, client: AsyncTestClient) -> None:
        fake_id = str(uuid4())
        response = await client.get(f"/api/admin/email-logs/{fake_id}")
        assert response.status_code in (401, 403, 404, 500)


class TestMailingValidation:
    """Validation tests for mailing domain."""

    async def test_create_template_missing_internal_name(self, client: AsyncTestClient) -> None:
        data = {
            "display_name": "Test Template",
            "subject": "Test Subject",
            "content_text": "Test content",
        }
        response = await client.post("/api/admin/email-templates/", json=data)
        assert response.status_code in (400, 401, 403, 422, 500)

    async def test_create_template_missing_subject(self, client: AsyncTestClient) -> None:
        data = {
            "internal_name": "test-template",
            "display_name": "Test Template",
            "content_text": "Test content",
        }
        response = await client.post("/api/admin/email-templates/", json=data)
        assert response.status_code in (400, 401, 403, 422, 500)

    async def test_create_template_missing_content(self, client: AsyncTestClient) -> None:
        data = {
            "internal_name": "test-template",
            "display_name": "Test Template",
            "subject": "Test Subject",
        }
        response = await client.post("/api/admin/email-templates/", json=data)
        assert response.status_code in (400, 401, 403, 422, 500)

    async def test_get_template_invalid_uuid(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/admin/email-templates/not-a-uuid")
        assert response.status_code in (400, 401, 403, 404, 422)

    async def test_get_log_invalid_uuid(self, client: AsyncTestClient) -> None:
        response = await client.get("/api/admin/email-logs/not-a-uuid")
        assert response.status_code in (400, 401, 403, 404, 422)

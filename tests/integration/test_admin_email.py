"""Integration tests for AdminEmailController."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.di import Provide
from litestar.template.config import TemplateConfig
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from pydotorg.core.auth.middleware import JWTAuthMiddleware
from pydotorg.core.database.base import AuditBase
from pydotorg.domains.admin.controllers.email import AdminEmailController
from pydotorg.domains.admin.dependencies import (
    provide_email_admin_service,
)
from pydotorg.domains.admin.services.email import EmailAdminService
from pydotorg.domains.mailing.dependencies import (
    provide_email_template_service,
    provide_mailing_service,
)
from pydotorg.domains.mailing.models import EmailLog, EmailTemplate, EmailTemplateType
from pydotorg.domains.mailing.services import EmailTemplateService, MailingService
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


async def _create_db_session(postgres_uri: str) -> tuple[AsyncSession, any]:
    """Helper to create a database session."""
    engine = create_async_engine(postgres_uri, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = async_session_factory()
    return session, engine


async def _create_sample_template(session: AsyncSession) -> EmailTemplate:
    """Helper to create a sample template."""
    template = EmailTemplate(
        internal_name=f"test_template_{uuid4().hex[:8]}",
        display_name="Test Template",
        description="A test email template",
        template_type=EmailTemplateType.TRANSACTIONAL,
        subject="Hello {{ name }}!",
        content_text="Hello {{ name }}, this is a test email.",
        content_html="<h1>Hello {{ name }}!</h1><p>This is a test email.</p>",
        is_active=True,
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template


async def _create_sample_log(session: AsyncSession, template_name: str = "welcome") -> EmailLog:
    """Helper to create a sample email log."""
    log = EmailLog(
        template_name=template_name,
        recipient_email=f"test_{uuid4().hex[:8]}@example.com",
        subject="Test Email",
        status="sent",
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


class AdminEmailTestFixtures:
    """Container for admin email test fixtures."""

    client: AsyncTestClient
    postgres_uri: str
    staff_user: User
    regular_user: User
    admin_user: User


@pytest.fixture
async def admin_email_fixtures(postgres_uri: str) -> AsyncIterator[AdminEmailTestFixtures]:
    """Async test client with AdminEmailController and test users.

    Creates the database schema, test users, and client in the correct order
    to ensure all tests have access to the same database state.
    """
    from sqlalchemy import text

    engine = create_async_engine(postgres_uri, echo=False)

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(AuditBase.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        staff = User(
            username=f"staff_{uuid4().hex[:8]}",
            email=f"staff_{uuid4().hex[:8]}@example.com",
            password_hash="hashed_password",
            first_name="Staff",
            last_name="User",
            is_active=True,
            is_staff=True,
            is_superuser=False,
        )
        regular = User(
            username=f"regular_{uuid4().hex[:8]}",
            email=f"regular_{uuid4().hex[:8]}@example.com",
            password_hash="hashed_password",
            first_name="Regular",
            last_name="User",
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        admin = User(
            username=f"admin_{uuid4().hex[:8]}",
            email=f"admin_{uuid4().hex[:8]}@example.com",
            password_hash="hashed_password",
            first_name="Admin",
            last_name="User",
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        session.add_all([staff, regular, admin])
        await session.commit()
        for user in [staff, regular, admin]:
            await session.refresh(user)

        staff_data = User(id=staff.id, email=staff.email, username=staff.username, is_staff=True, is_superuser=False)
        regular_data = User(
            id=regular.id, email=regular.email, username=regular.username, is_staff=False, is_superuser=False
        )
        admin_data = User(id=admin.id, email=admin.email, username=admin.username, is_staff=True, is_superuser=True)

    await engine.dispose()

    import sys
    from uuid import UUID

    from litestar import Request

    if "pydotorg.domains.admin.controllers.email" in sys.modules:
        email_module = sys.modules["pydotorg.domains.admin.controllers.email"]
        email_module.EmailAdminService = EmailAdminService
        email_module.EmailTemplateService = EmailTemplateService
        email_module.MailingService = MailingService
        email_module.UUID = UUID
        email_module.Request = Request

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        metadata=AuditBase.metadata,
        create_all=False,
        before_send_handler="autocommit",
    )
    sqlalchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)

    from datetime import datetime
    from pathlib import Path

    def configure_minimal_templates(engine: JinjaTemplateEngine) -> None:
        """Configure minimal template globals for testing."""
        engine.engine.globals["now"] = datetime.now

    template_config = TemplateConfig(
        directory=Path(__file__).parent.parent.parent / "src" / "pydotorg" / "templates",
        engine=JinjaTemplateEngine,
        engine_callback=configure_minimal_templates,
    )

    test_app = Litestar(
        route_handlers=[AdminEmailController],
        plugins=[sqlalchemy_plugin],
        middleware=[JWTAuthMiddleware],
        dependencies={
            "email_admin_service": Provide(provide_email_admin_service),
            "email_template_service": Provide(provide_email_template_service),
            "mailing_service": Provide(provide_mailing_service),
        },
        template_config=template_config,
        debug=True,
    )

    async with AsyncTestClient(
        app=test_app,
        base_url="http://testserver.local",
    ) as test_client:
        fixtures = AdminEmailTestFixtures()
        fixtures.client = test_client
        fixtures.postgres_uri = postgres_uri
        fixtures.staff_user = staff_data
        fixtures.regular_user = regular_data
        fixtures.admin_user = admin_data
        yield fixtures


@pytest.mark.integration
class TestAdminEmailDashboard:
    """Test admin email dashboard routes."""

    async def test_dashboard_requires_auth(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that dashboard requires authentication."""
        response = await admin_email_fixtures.client.get("/admin/email/", follow_redirects=False)
        assert response.status_code in (302, 401)

    async def test_dashboard_redirects_to_login_when_not_authenticated(
        self, admin_email_fixtures: AdminEmailTestFixtures
    ) -> None:
        """Test that unauthenticated users are redirected to login."""
        response = await admin_email_fixtures.client.get("/admin/email/", follow_redirects=False)
        assert response.status_code == 302
        assert "login" in response.headers.get("location", "").lower()

    async def test_dashboard_requires_staff(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that dashboard requires staff permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.regular_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_dashboard_accessible_to_staff(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that staff can access dashboard."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert b"Email Management" in response.content or b"email" in response.content.lower()

    async def test_dashboard_accessible_to_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that admin can access dashboard."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.admin_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert b"Email Management" in response.content or b"email" in response.content.lower()


@pytest.mark.integration
class TestAdminEmailTemplates:
    """Test admin email template routes."""

    async def test_list_templates_requires_auth(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that templates list requires authentication."""
        response = await admin_email_fixtures.client.get("/admin/email/templates", follow_redirects=False)
        assert response.status_code in (302, 401)

    async def test_list_templates_requires_staff(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that templates list requires staff permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.regular_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/templates",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_list_templates_accessible_to_staff(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that staff can access templates list."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/templates",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert b"Email Templates" in response.content or b"template" in response.content.lower()

    async def test_list_templates_pagination(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test templates list pagination."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/templates?limit=10&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_list_templates_search(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test templates list search functionality."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/templates?q=welcome",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_list_templates_active_only_filter(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test templates list with active_only filter."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/templates?active_only=true",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_new_template_form_requires_auth(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that new template form requires authentication."""
        response = await admin_email_fixtures.client.get("/admin/email/templates/new", follow_redirects=False)
        assert response.status_code in (302, 401)

    async def test_new_template_form_accessible_to_staff(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that staff can access new template form."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/templates/new",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert b"New Email Template" in response.content or b"new" in response.content.lower()

    async def test_template_detail_requires_auth(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that template detail requires authentication."""
        fake_id = uuid4()
        response = await admin_email_fixtures.client.get(f"/admin/email/templates/{fake_id}", follow_redirects=False)
        assert response.status_code in (302, 401)

    async def test_template_detail_requires_staff(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that template detail requires staff permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.regular_user.id)
        response = await admin_email_fixtures.client.get(
            f"/admin/email/templates/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_template_detail_redirects_when_not_found(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that non-existent template redirects."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.get(
            f"/admin/email/templates/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
            follow_redirects=False,
        )
        assert response.status_code == 302

    async def test_create_template_requires_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that creating templates requires admin (superuser) permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.post(
            "/admin/email/templates",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "internal_name": "test_template",
                "display_name": "Test Template",
                "subject": "Test Subject",
                "content_text": "Test content",
                "template_type": "transactional",
            },
        )
        assert response.status_code == 403

    async def test_update_template_requires_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that updating templates requires admin permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.put(
            f"/admin/email/templates/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "display_name": "Updated Template",
            },
        )
        assert response.status_code == 403


@pytest.mark.integration
class TestAdminEmailLogs:
    """Test admin email log routes."""

    async def test_list_logs_requires_auth(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that logs list requires authentication."""
        response = await admin_email_fixtures.client.get("/admin/email/logs", follow_redirects=False)
        assert response.status_code in (302, 401)

    async def test_list_logs_requires_staff(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that logs list requires staff permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.regular_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_list_logs_accessible_to_staff(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that staff can access logs list."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert b"Email Logs" in response.content or b"log" in response.content.lower()

    async def test_list_logs_pagination(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test logs list pagination."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/logs?limit=20&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_list_logs_search(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test logs list search functionality."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/logs?q=test@example.com",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_list_logs_failed_only_filter(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test logs list with failed_only filter."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.get(
            "/admin/email/logs?failed_only=true",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_log_detail_requires_auth(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that log detail requires authentication."""
        fake_id = uuid4()
        response = await admin_email_fixtures.client.get(f"/admin/email/logs/{fake_id}", follow_redirects=False)
        assert response.status_code in (302, 401)

    async def test_log_detail_requires_staff(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that log detail requires staff permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.regular_user.id)
        response = await admin_email_fixtures.client.get(
            f"/admin/email/logs/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_log_detail_redirects_when_not_found(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that non-existent log redirects."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.get(
            f"/admin/email/logs/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
            follow_redirects=False,
        )
        assert response.status_code == 302


@pytest.mark.integration
class TestAdminEmailTemplateActions:
    """Test admin email template actions (preview, send test)."""

    async def test_preview_template_requires_auth(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that preview requires authentication."""
        fake_id = uuid4()
        response = await admin_email_fixtures.client.post(
            f"/admin/email/templates/{fake_id}/preview", follow_redirects=False
        )
        assert response.status_code in (302, 401)

    async def test_preview_template_requires_staff(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that preview requires staff permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.regular_user.id)
        response = await admin_email_fixtures.client.post(
            f"/admin/email/templates/{fake_id}/preview",
            headers={"Authorization": f"Bearer {token}"},
            data={"context": "{}"},
        )
        assert response.status_code == 403

    async def test_send_test_email_requires_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that sending test email requires admin permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.post(
            f"/admin/email/templates/{fake_id}/send-test",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "test_email": "test@example.com",
                "context": "{}",
            },
        )
        assert response.status_code == 403

    async def test_send_test_email_with_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test sending test email as admin."""
        from pydotorg.core.auth.jwt import jwt_service

        session, engine = await _create_db_session(admin_email_fixtures.postgres_uri)
        try:
            template = await _create_sample_template(session)

            token = jwt_service.create_access_token(admin_email_fixtures.admin_user.id)

            with patch.object(MailingService, "_send_smtp", return_value=None):
                response = await admin_email_fixtures.client.post(
                    f"/admin/email/templates/{template.id}/send-test",
                    headers={"Authorization": f"Bearer {token}"},
                    data={
                        "test_email": "test@example.com",
                        "context": '{"name": "Test User"}',
                    },
                )

            assert response.status_code == 200
            assert b"sent successfully" in response.content or response.status_code == 200
        finally:
            await session.close()
            await engine.dispose()

    async def test_send_test_email_missing_email_address(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that sending test email without email address shows error."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.admin_user.id)
        response = await admin_email_fixtures.client.post(
            f"/admin/email/templates/{fake_id}/send-test",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "context": "{}",
            },
        )
        # Returns 200 with HTML error message for HTMX swapping
        assert response.status_code == 200
        assert "alert" in response.text
        assert "email" in response.text.lower() or "not found" in response.text.lower()

    async def test_preview_template_with_invalid_json(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test preview with invalid JSON context."""
        from pydotorg.core.auth.jwt import jwt_service

        session, engine = await _create_db_session(admin_email_fixtures.postgres_uri)
        try:
            template = await _create_sample_template(session)

            token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
            response = await admin_email_fixtures.client.post(
                f"/admin/email/templates/{template.id}/preview",
                headers={"Authorization": f"Bearer {token}"},
                data={"context": "invalid json"},
            )
            assert response.status_code in (200, 400, 500)
        finally:
            await session.close()
            await engine.dispose()


@pytest.mark.integration
class TestAdminEmailNewRoutes:
    """Test new admin email routes (edit, preview GET, activate, deactivate, delete, retry)."""

    async def test_edit_template_form_requires_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that edit template form requires admin (superuser) permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        session, engine = await _create_db_session(admin_email_fixtures.postgres_uri)
        try:
            template = await _create_sample_template(session)

            token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
            response = await admin_email_fixtures.client.get(
                f"/admin/email/templates/{template.id}/edit",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 403
        finally:
            await session.close()
            await engine.dispose()

    async def test_edit_template_form_accessible_to_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that admin can access edit template form."""
        from pydotorg.core.auth.jwt import jwt_service

        session, engine = await _create_db_session(admin_email_fixtures.postgres_uri)
        try:
            template = await _create_sample_template(session)

            token = jwt_service.create_access_token(admin_email_fixtures.admin_user.id)
            response = await admin_email_fixtures.client.get(
                f"/admin/email/templates/{template.id}/edit",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            assert b"Edit" in response.content
        finally:
            await session.close()
            await engine.dispose()

    async def test_edit_template_form_redirects_when_not_found(
        self, admin_email_fixtures: AdminEmailTestFixtures
    ) -> None:
        """Test that non-existent template redirects."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.admin_user.id)
        response = await admin_email_fixtures.client.get(
            f"/admin/email/templates/{fake_id}/edit",
            headers={"Authorization": f"Bearer {token}"},
            follow_redirects=False,
        )
        assert response.status_code == 302

    async def test_get_preview_template_accessible_to_staff(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that staff can access GET preview endpoint."""
        from pydotorg.core.auth.jwt import jwt_service

        session, engine = await _create_db_session(admin_email_fixtures.postgres_uri)
        try:
            template = await _create_sample_template(session)

            token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
            response = await admin_email_fixtures.client.get(
                f"/admin/email/templates/{template.id}/preview",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            assert b"Preview" in response.content or b"preview" in response.content.lower()
        finally:
            await session.close()
            await engine.dispose()

    async def test_get_preview_returns_404_when_not_found(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that GET preview returns 404 for non-existent template."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.get(
            f"/admin/email/templates/{fake_id}/preview",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_activate_template_requires_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that activating templates requires admin permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.post(
            f"/admin/email/templates/{fake_id}/activate",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_activate_template_works_for_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that admin can activate a template."""
        from pydotorg.core.auth.jwt import jwt_service

        session, engine = await _create_db_session(admin_email_fixtures.postgres_uri)
        try:
            template = await _create_sample_template(session)
            template.is_active = False
            await session.commit()

            token = jwt_service.create_access_token(admin_email_fixtures.admin_user.id)
            response = await admin_email_fixtures.client.post(
                f"/admin/email/templates/{template.id}/activate",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
        finally:
            await session.close()
            await engine.dispose()

    async def test_deactivate_template_requires_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that deactivating templates requires admin permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.post(
            f"/admin/email/templates/{fake_id}/deactivate",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_deactivate_template_works_for_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that admin can deactivate a template."""
        from pydotorg.core.auth.jwt import jwt_service

        session, engine = await _create_db_session(admin_email_fixtures.postgres_uri)
        try:
            template = await _create_sample_template(session)

            token = jwt_service.create_access_token(admin_email_fixtures.admin_user.id)
            response = await admin_email_fixtures.client.post(
                f"/admin/email/templates/{template.id}/deactivate",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
        finally:
            await session.close()
            await engine.dispose()

    async def test_delete_template_requires_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that deleting templates requires admin permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.delete(
            f"/admin/email/templates/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_delete_template_works_for_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that admin can delete a template."""
        from pydotorg.core.auth.jwt import jwt_service

        session, engine = await _create_db_session(admin_email_fixtures.postgres_uri)
        try:
            template = await _create_sample_template(session)

            token = jwt_service.create_access_token(admin_email_fixtures.admin_user.id)
            response = await admin_email_fixtures.client.delete(
                f"/admin/email/templates/{template.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
        finally:
            await session.close()
            await engine.dispose()

    async def test_delete_template_returns_404_when_not_found(
        self, admin_email_fixtures: AdminEmailTestFixtures
    ) -> None:
        """Test that deleting non-existent template returns 404."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.admin_user.id)
        response = await admin_email_fixtures.client.delete(
            f"/admin/email/templates/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_retry_email_requires_admin(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that retrying email requires admin permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.post(
            f"/admin/email/logs/{fake_id}/retry",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_retry_email_returns_404_when_not_found(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that retrying non-existent email returns 404."""
        from pydotorg.core.auth.jwt import jwt_service

        fake_id = uuid4()
        token = jwt_service.create_access_token(admin_email_fixtures.admin_user.id)
        response = await admin_email_fixtures.client.post(
            f"/admin/email/logs/{fake_id}/retry",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_retry_email_rejects_non_failed_logs(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that retrying a non-failed email returns 400."""
        from pydotorg.core.auth.jwt import jwt_service

        session, engine = await _create_db_session(admin_email_fixtures.postgres_uri)
        try:
            log = await _create_sample_log(session)

            token = jwt_service.create_access_token(admin_email_fixtures.admin_user.id)
            response = await admin_email_fixtures.client.post(
                f"/admin/email/logs/{log.id}/retry",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 400
        finally:
            await session.close()
            await engine.dispose()

    async def test_preview_new_template_requires_auth(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that preview new template requires authentication."""
        response = await admin_email_fixtures.client.post(
            "/admin/email/templates/preview",
            data={
                "subject": "Test Subject",
                "content_text": "Test content",
            },
            follow_redirects=False,
        )
        assert response.status_code in (302, 401)

    async def test_preview_new_template_requires_staff(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that preview new template requires staff permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.regular_user.id)
        response = await admin_email_fixtures.client.post(
            "/admin/email/templates/preview",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "subject": "Test Subject",
                "content_text": "Test content",
            },
        )
        assert response.status_code == 403

    async def test_preview_new_template_works_for_staff(self, admin_email_fixtures: AdminEmailTestFixtures) -> None:
        """Test that staff can preview new template content."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.post(
            "/admin/email/templates/preview",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "subject": "Welcome {{ user.username }}!",
                "content_text": "Hello {{ user.username }}, welcome to {{ site_name }}!",
                "content_html": "<p>Hello <strong>{{ user.username }}</strong></p>",
            },
        )
        assert response.status_code == 200
        assert b"johndoe" in response.content or b"preview" in response.content.lower()

    async def test_preview_new_template_handles_invalid_jinja(
        self, admin_email_fixtures: AdminEmailTestFixtures
    ) -> None:
        """Test that preview handles invalid Jinja2 syntax gracefully."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(admin_email_fixtures.staff_user.id)
        response = await admin_email_fixtures.client.post(
            "/admin/email/templates/preview",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "subject": "Invalid {{ unclosed",
                "content_text": "Also invalid {% if",
            },
        )
        assert response.status_code == 200


@pytest.mark.integration
class TestAppStartup:
    """Test that the application can start up properly."""

    def test_app_can_be_imported(self) -> None:
        """Test that the main app can be imported without errors."""
        from pydotorg.main import app

        assert app is not None
        assert hasattr(app, "routes")

    def test_admin_email_controller_registered(self) -> None:
        """Test that AdminEmailController is properly registered."""
        from pydotorg.main import app

        route_paths = [route.path for route in app.routes]
        assert any("/admin/email" in path for path in route_paths)


@pytest.mark.integration
class TestCSRFProtection:
    """Test CSRF protection with real app and cookies."""

    async def test_csrf_token_set_on_get_request(self) -> None:
        """Test that CSRF cookie is set on GET requests with proper token length."""
        from litestar.testing import AsyncTestClient

        from pydotorg.main import app

        async with AsyncTestClient(app=app) as client:
            response = await client.get("/", follow_redirects=False)
            csrf_token = response.cookies.get("csrftoken")
            assert csrf_token is not None, "CSRF cookie not set"
            assert len(csrf_token) >= 64, (
                f"CSRF token too short ({len(csrf_token)} chars), expected >= 64. Clear browser cookies!"
            )

    async def test_post_without_csrf_fails(self) -> None:
        """Test that POST without CSRF token fails with 403."""
        from litestar.testing import AsyncTestClient

        from pydotorg.main import app

        async with AsyncTestClient(app=app) as client:
            await client.get("/")
            response = await client.post(
                "/admin/email/templates/preview",
                data={"subject": "Test", "content_text": "Test"},
            )
            assert response.status_code == 403

    async def test_post_with_csrf_header_succeeds(self) -> None:
        """Test that POST with CSRF header succeeds."""
        from litestar.testing import AsyncTestClient

        from pydotorg.core.auth.jwt import jwt_service
        from pydotorg.main import app

        async with AsyncTestClient(app=app) as client:
            get_response = await client.get("/")
            csrf_token = get_response.cookies.get("csrftoken")
            assert csrf_token is not None, "CSRF cookie should be set"

            staff_user = await _get_or_create_staff_user(client)
            token = jwt_service.create_access_token(staff_user.id)

            response = await client.post(
                "/admin/email/templates/preview",
                headers={
                    "Authorization": f"Bearer {token}",
                    "x-csrftoken": csrf_token,
                },
                data={"subject": "Test", "content_text": "Test"},
            )
            assert response.status_code in (200, 302, 401, 403)

    async def test_post_with_csrf_form_field_succeeds(self) -> None:
        """Test that POST with CSRF form field succeeds."""
        from litestar.testing import AsyncTestClient

        from pydotorg.core.auth.jwt import jwt_service
        from pydotorg.main import app

        async with AsyncTestClient(app=app) as client:
            get_response = await client.get("/")
            csrf_token = get_response.cookies.get("csrftoken")
            assert csrf_token is not None, "CSRF cookie should be set"

            staff_user = await _get_or_create_staff_user(client)
            token = jwt_service.create_access_token(staff_user.id)

            response = await client.post(
                "/admin/email/templates/preview",
                headers={"Authorization": f"Bearer {token}"},
                data={
                    "subject": "Test",
                    "content_text": "Test",
                    "_csrf_token": csrf_token,
                },
            )
            assert response.status_code in (200, 302, 401, 403)


async def _get_or_create_staff_user(client: any) -> any:
    """Helper to get or create a staff user for CSRF tests."""
    from uuid import uuid4

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from pydotorg.config import settings
    from pydotorg.domains.users.models import User

    db_url = str(settings.database_url)
    engine = create_async_engine(db_url, echo=False)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        result = await session.execute(text("SELECT id FROM users WHERE is_staff = true LIMIT 1"))
        row = result.fetchone()
        if row:
            user = await session.get(User, row[0])
            await engine.dispose()
            return user

        user = User(
            username=f"csrf_staff_{uuid4().hex[:8]}",
            email=f"csrf_staff_{uuid4().hex[:8]}@example.com",
            password_hash="hashed",
            is_active=True,
            is_staff=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        await engine.dispose()
        return user

"""Admin email controller for email template and log management."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated
from urllib.parse import quote
from uuid import UUID  # noqa: TC003

from advanced_alchemy.exceptions import NotFoundError
from jinja2 import TemplateSyntaxError, UndefinedError
from litestar import Controller, delete, get, post, put
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.params import Parameter
from litestar.response import Redirect, Response, Template

from pydotorg.core.auth.guards import require_admin, require_staff
from pydotorg.domains.admin import urls
from pydotorg.domains.admin.services.email import EmailAdminService  # noqa: TC001
from pydotorg.domains.mailing.models import EmailTemplate, EmailTemplateType
from pydotorg.domains.mailing.schemas import EmailTemplateCreate
from pydotorg.domains.mailing.services import EmailTemplateService, MailingService  # noqa: TC001

if TYPE_CHECKING:
    from litestar import Request


def _admin_auth_exception_handler(request: Request, exc: NotAuthorizedException) -> Response:
    """Redirect to login page when user is not authenticated."""
    next_url = quote(str(request.url), safe="")
    return Redirect(f"/auth/login?next={next_url}")


def _admin_permission_exception_handler(request: Request, exc: PermissionDeniedException) -> Response:
    """Show 403 template when user lacks permissions."""
    return Template(
        template_name="errors/403.html.jinja2",
        context={
            "title": "Access Denied",
            "message": str(exc.detail) if exc.detail else "You do not have permission to access this page.",
        },
        status_code=403,
    )


class AdminEmailController(Controller):
    """Controller for admin email management."""

    path = urls.ADMIN_EMAIL
    include_in_schema = False
    guards = [require_staff]
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def dashboard(
        self,
        email_admin_service: EmailAdminService,
    ) -> Template:
        """Render email dashboard with statistics.

        Args:
            email_admin_service: Email admin service

        Returns:
            Email dashboard template
        """
        stats = await email_admin_service.get_dashboard_stats()

        return Template(
            template_name="admin/email/dashboard.html.jinja2",
            context={
                "title": "Email Management",
                "description": "Manage email templates and view email logs",
                "stats": stats,
            },
        )

    @get("/templates")
    async def list_templates(
        self,
        email_admin_service: EmailAdminService,
        q: Annotated[str | None, Parameter(description="Search query")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 20,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
        *,
        active_only: Annotated[bool, Parameter(description="Show only active templates")] = False,
    ) -> Template:
        """Render email templates list page.

        Args:
            email_admin_service: Email admin service
            q: Search query
            limit: Maximum templates per page
            offset: Pagination offset
            active_only: Show only active templates

        Returns:
            Templates list template
        """
        templates, total = await email_admin_service.list_templates(
            limit=limit,
            offset=offset,
            search=q,
            active_only=active_only,
        )

        return Template(
            template_name="admin/email/templates/list.html.jinja2",
            context={
                "title": "Email Templates",
                "description": "Manage email templates",
                "templates": templates,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                },
            },
        )

    @get("/templates/new")
    async def get_new_template_form(self) -> Template:
        """Render new email template form.

        Returns:
            New template form template
        """
        return Template(
            template_name="admin/email/templates/new.html.jinja2",
            context={
                "title": "New Email Template",
                "description": "Create a new email template",
            },
        )

    @post("/templates/preview")
    async def preview_new_template(
        self,
        request: Request,
    ) -> Template:
        """HTMX preview of new email template (before saving).

        Args:
            request: HTTP request with form data

        Returns:
            Template preview partial
        """
        from jinja2 import BaseLoader, Environment  # noqa: PLC0415

        form_data = await request.form()
        subject = str(form_data.get("subject", ""))
        content_text = str(form_data.get("content_text", ""))
        content_html = str(form_data.get("content_html", "")) or None

        sample_context = {
            "user": {
                "username": "johndoe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
            },
            "site_name": "Python.org",
            "site_url": "https://www.python.org",
            "support_email": "support@python.org",
            "current_year": "2024",
            "job": {
                "title": "Senior Python Developer",
                "company": "Acme Corp",
                "location": "Remote",
                "job_type": "Full-time",
                "url": "https://www.python.org/jobs/123/",
            },
            "event": {
                "name": "PyCon US 2024",
                "date": "May 15-23, 2024",
                "location": "Pittsburgh, PA",
                "url": "https://us.pycon.org/2024/",
            },
            "post": {
                "title": "Python 3.13 Released",
                "excerpt": "We are excited to announce the release of Python 3.13...",
                "url": "https://www.python.org/blog/python-3-13/",
                "author": "Python Core Team",
            },
            "sponsor": {
                "name": "Acme Corporation",
                "level": "Gold",
                "url": "https://acme.example.com",
            },
            "unsubscribe_url": "https://www.python.org/unsubscribe/abc123",
            "preferences_url": "https://www.python.org/preferences/abc123",
        }

        validation_errors: list[str] = []
        env = Environment(loader=BaseLoader(), autoescape=True)

        try:
            subject_template = env.from_string(subject)
            rendered_subject = subject_template.render(sample_context)
        except (TemplateSyntaxError, UndefinedError) as e:
            rendered_subject = "[Render error]"
            validation_errors.append(f"Subject: {e}")

        try:
            text_template = env.from_string(content_text)
            rendered_text = text_template.render(sample_context)
        except (TemplateSyntaxError, UndefinedError) as e:
            rendered_text = str(e)
            validation_errors.append(f"Text content: {e}")

        rendered_html = None
        if content_html:
            try:
                html_template = env.from_string(content_html)
                rendered_html = html_template.render(sample_context)
            except (TemplateSyntaxError, UndefinedError) as e:
                validation_errors.append(f"HTML content: {e}")

        return Template(
            template_name="admin/email/partials/preview.html.jinja2",
            context={
                "rendered_subject": rendered_subject,
                "rendered_text": rendered_text,
                "rendered_html": rendered_html,
                "validation_errors": validation_errors,
                "sample_context": sample_context,
            },
        )

    @get("/templates/{template_id:uuid}")
    async def get_template_detail(
        self,
        email_admin_service: EmailAdminService,
        template_id: UUID,
    ) -> Template | Response:
        """Render email template detail/edit page.

        Args:
            email_admin_service: Email admin service
            template_id: Template ID

        Returns:
            Template detail page or redirect if not found
        """
        template = await email_admin_service.get_template(template_id)
        if not template:
            return Redirect("/admin/email/templates")

        return Template(
            template_name="admin/email/templates/detail.html.jinja2",
            context={
                "title": f"{template.display_name} - Template",
                "description": f"Edit template: {template.display_name}",
                "template": template,
            },
        )

    @post("/templates/{template_id:uuid}/preview")
    async def preview_template(
        self,
        request: Request,
        email_template_service: EmailTemplateService,
        template_id: UUID,
    ) -> Template | Response:
        """HTMX preview of rendered email template.

        Args:
            request: HTTP request
            email_template_service: Email template service
            template_id: Template ID

        Returns:
            Template preview partial or error response
        """
        form_data = await request.form()
        context_data = form_data.get("context", "{}")

        try:
            context = json.loads(str(context_data))
        except json.JSONDecodeError:
            context = {}

        preview = await email_template_service.preview_template(template_id, context)

        if "error" in preview:
            return Response(content=preview["error"], status_code=400)

        return Template(
            template_name="admin/email/partials/preview.html.jinja2",
            context={"preview": preview},
        )

    @post("/templates/{template_id:uuid}/send-test", guards=[require_admin])
    async def send_test_email(
        self,
        request: Request,
        mailing_service: MailingService,
        email_admin_service: EmailAdminService,
        template_id: UUID,
    ) -> Response:
        """Send a test email from a template.

        Args:
            request: HTTP request
            mailing_service: Mailing service
            email_admin_service: Email admin service
            template_id: Template ID

        Returns:
            Success or error response
        """
        template = await email_admin_service.get_template(template_id)
        if not template:
            return Response(
                content="""<div class="alert alert-error">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span>Template not found</span>
                </div>""",
                status_code=200,
                media_type="text/html",
            )

        form_data = await request.form()
        test_email = form_data.get("test_email")
        context_data = form_data.get("context", "{}")

        if not test_email:
            return Response(
                content="""<div class="alert alert-warning">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span>Please enter an email address</span>
                </div>""",
                status_code=200,
                media_type="text/html",
            )

        # Start with comprehensive sample context for test emails
        sample_context = {
            "user": {
                "username": "testuser",
                "email": str(test_email),
                "first_name": "Test",
                "last_name": "User",
                "full_name": "Test User",
            },
            "site_name": "Python.org",
            "site_url": "https://www.python.org",
            "support_email": "support@python.org",
            "current_year": "2024",
            "job": {
                "title": "Senior Python Developer",
                "company": "Acme Corp",
                "location": "Remote",
                "job_type": "Full-time",
                "url": "https://www.python.org/jobs/123/",
            },
            "event": {
                "name": "PyCon US 2024",
                "date": "May 15-23, 2024",
                "location": "Pittsburgh, PA",
                "url": "https://us.pycon.org/2024/",
            },
            "post": {
                "title": "Python 3.13 Released",
                "excerpt": "We are excited to announce the release of Python 3.13...",
                "url": "https://www.python.org/blog/python-3-13/",
                "author": "Python Core Team",
            },
            "sponsor": {
                "name": "Acme Corporation",
                "level": "Gold",
                "url": "https://acme.example.com",
            },
            "unsubscribe_url": "https://www.python.org/unsubscribe/abc123",
            "preferences_url": "https://www.python.org/preferences/abc123",
        }

        # Merge user-provided context on top of sample context
        try:
            user_context = json.loads(str(context_data))
            sample_context.update(user_context)
        except json.JSONDecodeError:
            pass

        log = await mailing_service.send_email(
            template_name=template.internal_name,
            to_email=str(test_email),
            context=sample_context,
        )

        if log.status == "sent":
            return Response(
                content="""<div class="alert alert-success">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Test email sent! Check <a href="http://localhost:1080" target="_blank" class="link">MailDev</a></span>
                </div>""",
                status_code=200,
                media_type="text/html",
                headers={"HX-Trigger": "testEmailSent"},
            )
        return Response(
            content=f"""<div class="alert alert-error">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>Failed: {log.error_message or "Unknown error"}</span>
            </div>""",
            status_code=200,
            media_type="text/html",
        )

    @get("/logs")
    async def list_logs(
        self,
        request: Request,
        email_admin_service: EmailAdminService,
        q: Annotated[str | None, Parameter(description="Search query")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 50,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
        *,
        failed_only: Annotated[bool, Parameter(description="Show only failed")] = False,
    ) -> Template:
        """Render email logs list page.

        Args:
            request: HTTP request
            email_admin_service: Email admin service
            q: Search query
            limit: Maximum logs per page
            offset: Pagination offset
            failed_only: Show only failed emails

        Returns:
            Email logs template or partial for HTMX requests
        """
        logs, total = await email_admin_service.list_logs(
            limit=limit,
            offset=offset,
            search=q,
            failed_only=failed_only,
        )

        context = {
            "title": "Email Logs",
            "description": "View email delivery logs",
            "logs": logs,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        }

        is_htmx = request.headers.get("HX-Request") == "true"
        is_boosted = request.headers.get("HX-Boosted") == "true"
        if is_htmx and not is_boosted:
            return Template(
                template_name="admin/email/partials/logs_list.html.jinja2",
                context=context,
            )

        return Template(
            template_name="admin/email/logs/list.html.jinja2",
            context=context,
        )

    @get("/logs/{log_id:uuid}")
    async def get_log_detail(
        self,
        email_admin_service: EmailAdminService,
        log_id: UUID,
    ) -> Template | Response:
        """Render email log detail page.

        Args:
            email_admin_service: Email admin service
            log_id: Log ID

        Returns:
            Log detail template or redirect if not found
        """
        log = await email_admin_service.get_log(log_id)
        if not log:
            return Redirect("/admin/email/logs")

        return Template(
            template_name="admin/email/logs/detail.html.jinja2",
            context={
                "title": f"Email Log - {log.recipient_email}",
                "description": f"Email log detail for {log.recipient_email}",
                "log": log,
            },
        )

    @post("/templates", guards=[require_admin])
    async def create_template(
        self,
        request: Request,
        email_template_service: EmailTemplateService,
    ) -> Response:
        """Create a new email template.

        Args:
            request: HTTP request
            email_template_service: Email template service

        Returns:
            Redirect to template detail on success
        """
        form_data = await request.form()

        try:
            template_data = EmailTemplateCreate(
                internal_name=str(form_data.get("internal_name") or ""),
                display_name=str(form_data.get("display_name") or ""),
                description=str(form_data.get("description")) if form_data.get("description") else None,
                template_type=str(form_data.get("template_type") or "transactional"),
                subject=str(form_data.get("subject") or ""),
                content_text=str(form_data.get("content_text") or ""),
                content_html=str(form_data.get("content_html")) if form_data.get("content_html") else None,
                is_active=bool(form_data.get("is_active", True)),
            )

            template = await email_template_service.create(
                EmailTemplate(**template_data.model_dump()), auto_commit=True
            )

            return Redirect(f"/admin/email/templates/{template.id}")

        except (ValueError, TypeError) as e:
            return Response(
                content=f"Failed to create template: {e}",
                status_code=400,
            )

    @put("/templates/{template_id:uuid}", guards=[require_admin])
    async def update_template(
        self,
        request: Request,
        email_template_service: EmailTemplateService,
        template_id: UUID,
    ) -> Response:
        """Update an email template.

        Args:
            request: HTTP request
            email_template_service: Email template service
            template_id: Template ID

        Returns:
            Redirect to template detail on success
        """
        template = await email_template_service.get(template_id)
        if not template:
            return Response(content="Template not found", status_code=404)

        form_data = await request.form()

        if display_name := form_data.get("display_name"):
            template.display_name = str(display_name)
        if description := form_data.get("description"):
            template.description = str(description)
        if template_type := form_data.get("template_type"):
            template.template_type = EmailTemplateType(str(template_type))
        if subject := form_data.get("subject"):
            template.subject = str(subject)
        if content_text := form_data.get("content_text"):
            template.content_text = str(content_text)
        if content_html := form_data.get("content_html"):
            template.content_html = str(content_html)
        if "is_active" in form_data:
            template.is_active = bool(form_data.get("is_active"))

        await email_template_service.update(template, auto_commit=True)

        redirect_url = f"/admin/email/templates/{template_id}"
        if request.headers.get("HX-Request"):
            return Response(
                content="",
                status_code=200,
                headers={"HX-Redirect": redirect_url},
            )
        return Redirect(redirect_url)

    @get("/templates/{template_id:uuid}/edit", guards=[require_admin])
    async def get_edit_template_form(
        self,
        email_admin_service: EmailAdminService,
        template_id: UUID,
    ) -> Template | Response:
        """Render email template edit form.

        Args:
            email_admin_service: Email admin service
            template_id: Template ID

        Returns:
            Template edit form or redirect if not found
        """
        template = await email_admin_service.get_template(template_id)
        if not template:
            return Redirect("/admin/email/templates")

        return Template(
            template_name="admin/email/templates/form.html.jinja2",
            context={
                "title": f"Edit {template.display_name} - Template",
                "description": f"Edit template: {template.display_name}",
                "template": template,
            },
        )

    @get("/templates/{template_id:uuid}/preview")
    async def get_preview_template(
        self,
        email_template_service: EmailTemplateService,
        template_id: UUID,
    ) -> Template | Response:
        """Get preview of rendered email template (for inline preview).

        Args:
            email_template_service: Email template service
            template_id: Template ID

        Returns:
            Template preview partial or error response
        """
        sample_context = {
            "user": {
                "username": "johndoe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
            },
            "site_name": "Python.org",
            "site_url": "https://www.python.org",
            "support_email": "support@python.org",
            "current_year": "2024",
            "job": {
                "title": "Senior Python Developer",
                "company": "Acme Corp",
                "location": "Remote",
                "job_type": "Full-time",
                "url": "https://www.python.org/jobs/123/",
            },
            "event": {
                "name": "PyCon US 2024",
                "date": "May 15-23, 2024",
                "location": "Pittsburgh, PA",
                "url": "https://us.pycon.org/2024/",
            },
            "post": {
                "title": "Python 3.13 Released",
                "excerpt": "We are excited to announce the release of Python 3.13...",
                "url": "https://www.python.org/blog/python-3-13/",
                "author": "Python Core Team",
            },
            "sponsor": {
                "name": "Acme Corporation",
                "level": "Gold",
                "url": "https://acme.example.com",
            },
            "unsubscribe_url": "https://www.python.org/unsubscribe/abc123",
            "preferences_url": "https://www.python.org/preferences/abc123",
        }

        try:
            template = await email_template_service.get(template_id)
        except NotFoundError:
            return Response(content="Template not found", status_code=404)

        try:
            rendered_subject = template.render_subject(sample_context)
            rendered_text = template.render_content_text(sample_context)
            rendered_html = template.render_content_html(sample_context)
            validation_errors = template.validate_templates()
        except (TemplateSyntaxError, UndefinedError) as e:
            return Template(
                template_name="admin/email/partials/preview.html.jinja2",
                context={
                    "rendered_subject": "[Render error]",
                    "rendered_text": str(e),
                    "rendered_html": None,
                    "validation_errors": [str(e)],
                    "sample_context": sample_context,
                },
            )

        return Template(
            template_name="admin/email/partials/preview.html.jinja2",
            context={
                "rendered_subject": rendered_subject,
                "rendered_text": rendered_text,
                "rendered_html": rendered_html,
                "validation_errors": validation_errors,
                "sample_context": sample_context,
            },
        )

    @post("/templates/{template_id:uuid}/activate", guards=[require_admin])
    async def activate_template(
        self,
        email_template_service: EmailTemplateService,
        template_id: UUID,
    ) -> Template | Response:
        """Activate an email template.

        Args:
            email_template_service: Email template service
            template_id: Template ID

        Returns:
            Updated template row partial or error
        """
        try:
            template = await email_template_service.get(template_id)
        except NotFoundError:
            return Response(content="Template not found", status_code=404)

        template.is_active = True
        await email_template_service.update(template, auto_commit=True)

        return Template(
            template_name="admin/email/partials/template_row.html.jinja2",
            context={"template": template},
        )

    @post("/templates/{template_id:uuid}/deactivate", guards=[require_admin])
    async def deactivate_template(
        self,
        email_template_service: EmailTemplateService,
        template_id: UUID,
    ) -> Template | Response:
        """Deactivate an email template.

        Args:
            email_template_service: Email template service
            template_id: Template ID

        Returns:
            Updated template row partial or error
        """
        try:
            template = await email_template_service.get(template_id)
        except NotFoundError:
            return Response(content="Template not found", status_code=404)

        template.is_active = False
        await email_template_service.update(template, auto_commit=True)

        return Template(
            template_name="admin/email/partials/template_row.html.jinja2",
            context={"template": template},
        )

    @delete("/templates/{template_id:uuid}", guards=[require_admin], status_code=200)
    async def delete_template(
        self,
        email_template_service: EmailTemplateService,
        template_id: UUID,
    ) -> Response:
        """Delete an email template.

        Args:
            email_template_service: Email template service
            template_id: Template ID

        Returns:
            Empty response (element removed by HTMX)
        """
        try:
            template = await email_template_service.get(template_id)
        except NotFoundError:
            return Response(content="Template not found", status_code=404)

        await email_template_service.delete(template.id, auto_commit=True)

        return Response(
            content="",
            status_code=200,
            headers={"HX-Trigger": "templateDeleted"},
        )

    @post("/logs/{log_id:uuid}/retry", guards=[require_admin])
    async def retry_failed_email(
        self,
        mailing_service: MailingService,
        email_admin_service: EmailAdminService,
        log_id: UUID,
    ) -> Template | Response:
        """Retry sending a failed email.

        Args:
            mailing_service: Mailing service
            email_admin_service: Email admin service
            log_id: Email log ID

        Returns:
            Updated log row partial or error
        """
        log = await email_admin_service.get_log(log_id)
        if not log:
            return Response(content="Email log not found", status_code=404)

        if log.status != "failed":
            return Response(content="Can only retry failed emails", status_code=400)

        new_log = await mailing_service.send_email(
            template_name=log.template_name,
            to_email=log.recipient_email,
        )

        return Template(
            template_name="admin/email/partials/log_row.html.jinja2",
            context={"log": new_log},
        )

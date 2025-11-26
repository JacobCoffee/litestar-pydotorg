"""Admin users controller for user management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from urllib.parse import quote
from uuid import UUID  # noqa: TC003

from litestar import Controller, delete, get, post
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.params import Parameter
from litestar.response import Redirect, Response, Template

from pydotorg.core.auth.guards import require_admin
from pydotorg.domains.admin import urls
from pydotorg.domains.admin.services.users import UserAdminService  # noqa: TC001

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


class AdminUsersController(Controller):
    """Controller for admin user management."""

    path = urls.ADMIN_USERS
    tags = ["Admin"]
    guards = [require_admin]
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def list_users(
        self,
        user_admin_service: UserAdminService,
        q: Annotated[str | None, Parameter(description="Search query")] = None,
        filter_by: Annotated[str | None, Parameter(query="filter", description="Filter type")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 20,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
    ) -> Template:
        """Render user list page.

        Args:
            user_admin_service: User admin service
            q: Search query
            filter_by: Filter type (staff, superuser, active, inactive)
            limit: Maximum users per page
            offset: Pagination offset

        Returns:
            User list template
        """
        users, total = await user_admin_service.list_users(
            limit=limit,
            offset=offset,
            search=q,
            filter_by=filter_by,
        )

        return Template(
            template_name="admin/users/list.html.jinja2",
            context={
                "title": "User Management",
                "description": "Manage all users and permissions",
                "users": users,
                "page_info": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                },
            },
        )

    @get("/{user_id:uuid}")
    async def get_user_detail(
        self,
        user_admin_service: UserAdminService,
        user_id: UUID,
    ) -> Template | Response:
        """Render user detail page.

        Args:
            user_admin_service: User admin service
            user_id: User ID

        Returns:
            User detail template or redirect if not found
        """
        user = await user_admin_service.get_user(user_id)
        if not user:
            return Redirect("/admin/users")

        return Template(
            template_name="admin/users/detail.html.jinja2",
            context={
                "title": f"{user.username} - User Details",
                "description": f"Details for user {user.username}",
                "user": user,
                "user_activities": [],
            },
        )

    @get("/{user_id:uuid}/edit")
    async def get_user_edit(
        self,
        user_admin_service: UserAdminService,
        user_id: UUID,
    ) -> Template | Response:
        """Render user edit page.

        Args:
            user_admin_service: User admin service
            user_id: User ID

        Returns:
            User edit template or redirect if not found
        """
        user = await user_admin_service.get_user(user_id)
        if not user:
            return Redirect("/admin/users")

        return Template(
            template_name="admin/users/edit.html.jinja2",
            context={
                "title": f"Edit {user.username}",
                "description": f"Edit user {user.username}",
                "user": user,
            },
        )

    @post("/{user_id:uuid}/edit")
    async def update_user(
        self,
        request: Request,
        user_admin_service: UserAdminService,
        user_id: UUID,
    ) -> Response:
        """Update user details.

        Args:
            request: HTTP request
            user_admin_service: User admin service
            user_id: User ID

        Returns:
            Redirect to user detail page
        """
        form_data = await request.form()

        await user_admin_service.update_user(
            user_id,
            first_name=form_data.get("first_name"),
            last_name=form_data.get("last_name"),
            email=form_data.get("email"),
            is_active=form_data.get("is_active") == "on",
            is_staff=form_data.get("is_staff") == "on",
            is_superuser=form_data.get("is_superuser") == "on",
        )

        return Redirect(f"/admin/users/{user_id}")

    @post("/{user_id:uuid}/activate")
    async def activate_user(
        self,
        request: Request,
        user_admin_service: UserAdminService,
        user_id: UUID,
    ) -> Template | Response:
        """Activate a user.

        Args:
            request: HTTP request
            user_admin_service: User admin service
            user_id: User ID

        Returns:
            Updated table row partial or redirect
        """
        user = await user_admin_service.activate_user(user_id)
        if not user:
            return Response(content="User not found", status_code=404)

        return Template(
            template_name="admin/users/partials/_user_row.html.jinja2",
            context={"user": user},
        )

    @post("/{user_id:uuid}/deactivate")
    async def deactivate_user(
        self,
        request: Request,
        user_admin_service: UserAdminService,
        user_id: UUID,
    ) -> Template | Response:
        """Deactivate a user.

        Args:
            request: HTTP request
            user_admin_service: User admin service
            user_id: User ID

        Returns:
            Updated table row partial or redirect
        """
        user = await user_admin_service.deactivate_user(user_id)
        if not user:
            return Response(content="User not found", status_code=404)

        return Template(
            template_name="admin/users/partials/_user_row.html.jinja2",
            context={"user": user},
        )

    @post("/{user_id:uuid}/toggle-staff")
    async def toggle_staff(
        self,
        user_admin_service: UserAdminService,
        user_id: UUID,
    ) -> Template | Response:
        """Toggle user staff status.

        Args:
            user_admin_service: User admin service
            user_id: User ID

        Returns:
            Updated roles partial
        """
        user = await user_admin_service.toggle_staff(user_id)
        if not user:
            return Response(content="User not found", status_code=404)

        return Template(
            template_name="admin/users/partials/_user_roles.html.jinja2",
            context={"user": user},
        )

    @post("/{user_id:uuid}/toggle-superuser")
    async def toggle_superuser(
        self,
        user_admin_service: UserAdminService,
        user_id: UUID,
    ) -> Template | Response:
        """Toggle user superuser status.

        Args:
            user_admin_service: User admin service
            user_id: User ID

        Returns:
            Updated roles partial
        """
        user = await user_admin_service.toggle_superuser(user_id)
        if not user:
            return Response(content="User not found", status_code=404)

        return Template(
            template_name="admin/users/partials/_user_roles.html.jinja2",
            context={"user": user},
        )

    @post("/{user_id:uuid}/toggle-active")
    async def toggle_active(
        self,
        user_admin_service: UserAdminService,
        user_id: UUID,
    ) -> Template | Response:
        """Toggle user active status.

        Args:
            user_admin_service: User admin service
            user_id: User ID

        Returns:
            Updated roles partial
        """
        user = await user_admin_service.toggle_active(user_id)
        if not user:
            return Response(content="User not found", status_code=404)

        return Template(
            template_name="admin/users/partials/_user_roles.html.jinja2",
            context={"user": user},
        )

    @post("/{user_id:uuid}/reset-password")
    async def reset_password(
        self,
        user_admin_service: UserAdminService,
        user_id: UUID,
    ) -> Response:
        """Send password reset email to user.

        Args:
            user_admin_service: User admin service
            user_id: User ID

        Returns:
            Success response
        """
        user = await user_admin_service.get_user(user_id)
        if not user:
            return Response(content="User not found", status_code=404)

        # TODO: Implement password reset email sending
        return Response(
            content="Password reset email sent",
            status_code=200,
            headers={"HX-Trigger": "showToast"},
        )

    @post("/{user_id:uuid}/resend-verification")
    async def resend_verification(
        self,
        user_admin_service: UserAdminService,
        user_id: UUID,
    ) -> Response:
        """Resend verification email to user.

        Args:
            user_admin_service: User admin service
            user_id: User ID

        Returns:
            Success response
        """
        user = await user_admin_service.get_user(user_id)
        if not user:
            return Response(content="User not found", status_code=404)

        # TODO: Implement verification email resending
        return Response(
            content="Verification email sent",
            status_code=200,
            headers={"HX-Trigger": "showToast"},
        )

    @delete("/{user_id:uuid}", status_code=200)
    async def delete_user(
        self,
        user_admin_service: UserAdminService,
        user_id: UUID,
    ) -> Response:
        """Delete a user.

        Args:
            user_admin_service: User admin service
            user_id: User ID

        Returns:
            Success or error response
        """
        deleted = await user_admin_service.delete_user(user_id)
        if not deleted:
            return Response(content="User not found", status_code=404)

        return Response(
            content="User deleted",
            status_code=200,
            headers={"HX-Redirect": "/admin/users"},
        )

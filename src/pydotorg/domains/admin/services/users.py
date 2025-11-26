"""User admin service for managing users in the admin panel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, or_, select

from pydotorg.domains.admin.schemas import AdminUserRead, UserStaffUpdate
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class UserAdminService:
    """Service for admin user management operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_users(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
        filter_by: str | None = None,
    ) -> tuple[list[User], int]:
        """List users with filtering and pagination.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            search: Search term for username or email
            filter_by: Filter type (staff, superuser, active, inactive)

        Returns:
            Tuple of (users list, total count)
        """
        base_stmt = select(User)
        count_stmt = select(func.count()).select_from(User)

        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
            )
            base_stmt = base_stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if filter_by:
            if filter_by == "staff":
                base_stmt = base_stmt.where(User.is_staff == True)  # noqa: E712
                count_stmt = count_stmt.where(User.is_staff == True)  # noqa: E712
            elif filter_by == "superuser":
                base_stmt = base_stmt.where(User.is_superuser == True)  # noqa: E712
                count_stmt = count_stmt.where(User.is_superuser == True)  # noqa: E712
            elif filter_by == "active":
                base_stmt = base_stmt.where(User.is_active == True)  # noqa: E712
                count_stmt = count_stmt.where(User.is_active == True)  # noqa: E712
            elif filter_by == "inactive":
                base_stmt = base_stmt.where(User.is_active == False)  # noqa: E712
                count_stmt = count_stmt.where(User.is_active == False)  # noqa: E712

        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = base_stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        users = list(result.scalars().all())

        return users, total

    async def get_user(self, user_id: UUID) -> User | None:
        """Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            User or None if not found
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user_status(
        self,
        user_id: UUID,
        data: UserStaffUpdate,
    ) -> User | None:
        """Update user staff/admin status.

        Args:
            user_id: User ID
            data: Update data

        Returns:
            Updated user or None if not found
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        if data.is_active is not None:
            user.is_active = data.is_active
        if data.is_staff is not None:
            user.is_staff = data.is_staff
        if data.is_superuser is not None:
            user.is_superuser = data.is_superuser

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def toggle_staff(self, user_id: UUID) -> User | None:
        """Toggle user staff status.

        Args:
            user_id: User ID

        Returns:
            Updated user or None if not found
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        user.is_staff = not user.is_staff
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def toggle_superuser(self, user_id: UUID) -> User | None:
        """Toggle user superuser status.

        Args:
            user_id: User ID

        Returns:
            Updated user or None if not found
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        user.is_superuser = not user.is_superuser
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def toggle_active(self, user_id: UUID) -> User | None:
        """Toggle user active status.

        Args:
            user_id: User ID

        Returns:
            Updated user or None if not found
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        user.is_active = not user.is_active
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def activate_user(self, user_id: UUID) -> User | None:
        """Activate a user.

        Args:
            user_id: User ID

        Returns:
            Updated user or None if not found
        """
        return await self.update_user_status(user_id, UserStaffUpdate(is_active=True))

    async def deactivate_user(self, user_id: UUID) -> User | None:
        """Deactivate a user.

        Args:
            user_id: User ID

        Returns:
            Updated user or None if not found
        """
        return await self.update_user_status(user_id, UserStaffUpdate(is_active=False))

    async def delete_user(self, user_id: UUID) -> bool:
        """Delete a user.

        Args:
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        user = await self.get_user(user_id)
        if not user:
            return False

        await self.session.delete(user)
        await self.session.commit()
        return True

    async def update_user(
        self,
        user_id: UUID,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        is_staff: bool | None = None,
        is_superuser: bool | None = None,
    ) -> User | None:
        """Update user details.

        Args:
            user_id: User ID
            first_name: New first name
            last_name: New last name
            email: New email
            is_active: Active status
            is_staff: Staff status
            is_superuser: Superuser status

        Returns:
            Updated user or None if not found
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if email is not None:
            user.email = email
        if is_active is not None:
            user.is_active = is_active
        if is_staff is not None:
            user.is_staff = is_staff
        if is_superuser is not None:
            user.is_superuser = is_superuser

        await self.session.commit()
        await self.session.refresh(user)
        return user

    def to_admin_read(self, user: User) -> AdminUserRead:
        """Convert a User model to AdminUserRead schema.

        Args:
            user: User model

        Returns:
            AdminUserRead schema
        """
        return AdminUserRead.model_validate(user)

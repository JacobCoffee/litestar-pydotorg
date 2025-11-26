"""Work Groups domain."""

from pydotorg.domains.work_groups.controllers import WorkGroupController, WorkGroupsPageController
from pydotorg.domains.work_groups.dependencies import get_work_groups_dependencies
from pydotorg.domains.work_groups.models import WorkGroup
from pydotorg.domains.work_groups.repositories import WorkGroupRepository
from pydotorg.domains.work_groups.schemas import (
    WorkGroupCreate,
    WorkGroupList,
    WorkGroupRead,
    WorkGroupUpdate,
)
from pydotorg.domains.work_groups.services import WorkGroupService

__all__ = [
    "WorkGroup",
    "WorkGroupController",
    "WorkGroupCreate",
    "WorkGroupList",
    "WorkGroupRead",
    "WorkGroupRepository",
    "WorkGroupService",
    "WorkGroupsPageController",
    "WorkGroupUpdate",
    "get_work_groups_dependencies",
]

"""Minutes domain."""

from pydotorg.domains.minutes.controllers import MinutesController, MinutesPageController
from pydotorg.domains.minutes.dependencies import get_minutes_dependencies
from pydotorg.domains.minutes.models import Minutes
from pydotorg.domains.minutes.repositories import MinutesRepository
from pydotorg.domains.minutes.schemas import (
    MinutesCreate,
    MinutesList,
    MinutesRead,
    MinutesUpdate,
)
from pydotorg.domains.minutes.services import MinutesService

__all__ = [
    "Minutes",
    "MinutesController",
    "MinutesCreate",
    "MinutesList",
    "MinutesPageController",
    "MinutesRead",
    "MinutesRepository",
    "MinutesService",
    "MinutesUpdate",
    "get_minutes_dependencies",
]

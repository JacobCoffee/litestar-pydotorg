"""Downloads domain."""

from pydotorg.domains.downloads.controllers import (
    DownloadsPageController,
    OSController,
    ReleaseController,
    ReleaseFileController,
)
from pydotorg.domains.downloads.dependencies import get_downloads_dependencies
from pydotorg.domains.downloads.models import OS, PythonVersion, Release, ReleaseFile
from pydotorg.domains.downloads.repositories import OSRepository, ReleaseFileRepository, ReleaseRepository
from pydotorg.domains.downloads.schemas import (
    DownloadPageData,
    OSCreate,
    OSRead,
    ReleaseCreate,
    ReleaseDetailPageData,
    ReleaseFileCreate,
    ReleaseFileRead,
    ReleaseFileWithOS,
    ReleaseList,
    ReleaseRead,
    ReleaseUpdate,
)
from pydotorg.domains.downloads.services import OSService, ReleaseFileService, ReleaseService

__all__ = [
    "OS",
    "DownloadPageData",
    "DownloadsPageController",
    "OSController",
    "OSCreate",
    "OSRead",
    "OSRepository",
    "OSService",
    "PythonVersion",
    "Release",
    "ReleaseController",
    "ReleaseCreate",
    "ReleaseDetailPageData",
    "ReleaseFile",
    "ReleaseFileController",
    "ReleaseFileCreate",
    "ReleaseFileRead",
    "ReleaseFileRepository",
    "ReleaseFileService",
    "ReleaseFileWithOS",
    "ReleaseList",
    "ReleaseRead",
    "ReleaseRepository",
    "ReleaseService",
    "ReleaseUpdate",
    "get_downloads_dependencies",
]

"""Downloads domain URL constants."""

from typing import Final

OS_LIST: Final[str] = "/api/v1/os"
OS_BY_ID: Final[str] = "/api/v1/os/{os_id:uuid}"

RELEASES: Final[str] = "/api/v1/releases"
RELEASE_BY_ID: Final[str] = "/api/v1/releases/{release_id:uuid}"
RELEASE_BY_SLUG: Final[str] = "/api/v1/releases/slug/{slug:str}"
LATEST_RELEASE: Final[str] = "/api/v1/releases/latest"
LATEST_BY_VERSION: Final[str] = "/api/v1/releases/latest/{version:str}"

RELEASE_FILES: Final[str] = "/api/v1/releases/{release_id:uuid}/files"
FILE_BY_ID: Final[str] = "/api/v1/files/{file_id:uuid}"

DOWNLOADS_INDEX: Final[str] = "/downloads/"
DOWNLOADS_RELEASE: Final[str] = "/downloads/release/{slug:str}/"
DOWNLOADS_SOURCE: Final[str] = "/downloads/source/"
DOWNLOADS_WINDOWS: Final[str] = "/downloads/windows/"
DOWNLOADS_MACOS: Final[str] = "/downloads/macos/"

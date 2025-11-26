"""Pages domain URL constants."""

from typing import Final

PAGES: Final[str] = "/api/v1/pages"
PAGE_BY_ID: Final[str] = "/api/v1/pages/{page_id:uuid}"
PAGE_BY_PATH: Final[str] = "/api/v1/pages/path"

PAGE_IMAGES: Final[str] = "/api/v1/pages/{page_id:uuid}/images"
IMAGE_BY_ID: Final[str] = "/api/v1/images/{image_id:uuid}"

PAGE_DOCUMENTS: Final[str] = "/api/v1/pages/{page_id:uuid}/documents"
DOCUMENT_BY_ID: Final[str] = "/api/v1/documents/{document_id:uuid}"

PAGE_PUBLISH: Final[str] = "/api/v1/pages/{page_id:uuid}/publish"
PAGE_UNPUBLISH: Final[str] = "/api/v1/pages/{page_id:uuid}/unpublish"
